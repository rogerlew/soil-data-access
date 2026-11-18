mod planner;
mod runtime;

use axum::{
    extract::{rejection::FormRejection, DefaultBodyLimit, State},
    http::{header, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Form, Json, Router,
};
use futures_util::StreamExt;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    time::Duration,
};
use tokio::{sync::Semaphore, task::JoinHandle, time::timeout};
use tokio_postgres::{types::ToSql, IsolationLevel, NoTls};

const MAX_BYTES: usize = 16 * 1024 * 1024;
const MAX_ROWS: usize = 100_000;

struct App {
    database_url: String,
    code_revision: String,
    slots: Semaphore,
    counter: AtomicU64,
    instance: u128,
}

#[derive(Clone, Copy)]
enum Failure {
    Invalid,
    Unsupported,
    Large,
    Overloaded,
    NotReady,
    Timeout,
    Internal,
}
impl Failure {
    fn response(self, request_id: &str) -> Response {
        let (status, code, message) = match self {
            Self::Invalid => (400, "invalid_request", "Invalid request"),
            Self::Unsupported => (
                422,
                "unsupported_query",
                "Query is outside the supported profile",
            ),
            Self::Large => (
                413,
                "request_too_large",
                "Request or result exceeds profile bounds",
            ),
            Self::Overloaded => (503, "overloaded", "Concurrent request limit reached"),
            Self::NotReady => (503, "not_ready", "No validated release is active"),
            Self::Timeout => (504, "query_timeout", "Operation deadline exceeded"),
            Self::Internal => (500, "internal_error", "Database operation failed"),
        };
        eprintln!(
            "{}",
            json!({"request_id":request_id,"error_code":code,"status":status})
        );
        (
            StatusCode::from_u16(status).unwrap(),
            Json(json!({"error":{"code":code,"message":message,"request_id":request_id}})),
        )
            .into_response()
    }
}

fn db_error(error: tokio_postgres::Error) -> Failure {
    if error.code().is_some_and(|code| code.code() == "57014") {
        Failure::Timeout
    } else {
        Failure::Internal
    }
}

struct ConnectionTask(JoinHandle<()>);
impl Drop for ConnectionTask {
    fn drop(&mut self) {
        self.0.abort();
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct QueryForm {
    query: String,
    format: String,
}

impl App {
    fn request_id(&self) -> String {
        format!(
            "{:x}-{}",
            self.instance,
            self.counter.fetch_add(1, Ordering::Relaxed)
        )
    }
}

async fn execute(
    app: &App,
    plan: Option<planner::Plan>,
    request_id: &str,
) -> Result<Response, Failure> {
    let (mut client, connection) = timeout(
        Duration::from_secs(3),
        tokio_postgres::connect(&app.database_url, NoTls),
    )
    .await
    .map_err(|_| Failure::Timeout)?
    .map_err(db_error)?;
    let _connection = ConnectionTask(tokio::spawn(async move {
        let _ = connection.await;
    }));
    // A new connection per operation avoids reusing a cancelled/aborted transaction.
    let transaction = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await
        .map_err(db_error)?;
    transaction.batch_execute("SET LOCAL statement_timeout='5s'; SET LOCAL idle_in_transaction_session_timeout='5s'; SET LOCAL search_path=pg_catalog")
        .await.map_err(db_error)?;
    let active = transaction.query_opt("SELECT r.id,r.manifest FROM soil.release r JOIN soil.active_release a ON a.release_id=r.id WHERE a.singleton", &[])
        .await.map_err(db_error)?;
    let Some(plan) = plan else {
        let manifest: Option<Value> = active.map(|row| row.get(1));
        return Ok(Json(json!({"service":"soil-data-access","official":false,"contract_version":"wepppy-json-v1",
            "code_revision":app.code_revision,"ready":manifest.is_some(),"active_release":manifest})).into_response());
    };
    let active = active.ok_or(Failure::NotReady)?;
    let release: String = active.get(0);
    let parameters: [&(dyn ToSql + Sync); 2] = [&release, &plan.keys];
    let stream = transaction
        .query_raw(&plan.family.postgres_sql, parameters)
        .await
        .map_err(db_error)?;
    futures_util::pin_mut!(stream);
    let mut body = b"{\"Table\":[".to_vec();
    serde_json::to_writer(&mut body, &plan.family.columns).map_err(|_| Failure::Internal)?;
    let mut count = 0;
    while let Some(row) = stream.next().await {
        let row = row.map_err(db_error)?;
        count += 1;
        if count > MAX_ROWS {
            return Err(Failure::Large);
        }
        let values = (0..row.len())
            .map(|i| row.try_get::<_, Option<String>>(i))
            .collect::<Result<Vec<_>, _>>()
            .map_err(db_error)?;
        let bytes = serde_json::to_vec(&values).map_err(|_| Failure::Internal)?;
        if body.len() + bytes.len() + 3 > MAX_BYTES {
            return Err(Failure::Large);
        }
        body.push(b',');
        body.extend(bytes);
    }
    body.extend(b"]}");
    eprintln!(
        "{}",
        json!({"request_id":request_id,"family":plan.family.family,"release":release,"rows":count,"status":200})
    );
    let release_header = release
        .parse::<header::HeaderValue>()
        .map_err(|_| Failure::Internal)?;
    Ok((
        [
            (
                header::CONTENT_TYPE,
                header::HeaderValue::from_static("application/json"),
            ),
            (
                header::HeaderName::from_static("x-soil-profile"),
                header::HeaderValue::from_static("wepppy-json-v1"),
            ),
            (
                header::HeaderName::from_static("x-soil-release"),
                release_header,
            ),
        ],
        body,
    )
        .into_response())
}

async fn dispatch(app: Arc<App>, plan: Option<planner::Plan>, id: String) -> Response {
    let Ok(_permit) = app.slots.try_acquire() else {
        return Failure::Overloaded.response(&id);
    };
    match timeout(Duration::from_secs(8), execute(&app, plan, &id)).await {
        Ok(Ok(response)) => response,
        Ok(Err(failure)) => failure.response(&id),
        Err(_) => Failure::Timeout.response(&id),
    }
}

async fn query(
    State(app): State<Arc<App>>,
    form: Result<Form<QueryForm>, FormRejection>,
) -> Response {
    let id = app.request_id();
    let form = match form {
        Ok(Form(form)) => form,
        Err(error) => {
            return if error.status() == StatusCode::PAYLOAD_TOO_LARGE {
                Failure::Large
            } else {
                Failure::Invalid
            }
            .response(&id)
        }
    };
    if form.format != "JSON+COLUMNNAME" {
        return Failure::Invalid.response(&id);
    }
    if form.query.len() > 65536 {
        return Failure::Large.response(&id);
    }
    let plan = match planner::admit(&form.query) {
        Ok(plan) => plan,
        Err(()) => return Failure::Unsupported.response(&id),
    };
    dispatch(app, Some(plan), id).await
}

async fn metadata(State(app): State<Arc<App>>) -> Response {
    let id = app.request_id();
    dispatch(app, None, id).await
}
async fn invalid(State(app): State<Arc<App>>) -> Response {
    Failure::Invalid.response(&app.request_id())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    if std::env::args().nth(1).as_deref() == Some("--healthcheck") {
        let release = std::env::var("SOIL_DATA_RELEASE").ok();
        return runtime::probe(
            "127.0.0.1:8080".parse()?,
            release.as_deref(),
            Duration::from_secs(3),
        )
        .map_err(|_| "Soil service is not ready".into());
    }
    let code_revision = std::env::var("CODE_REVISION")?;
    if code_revision.len() != 40
        || !code_revision
            .bytes()
            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
    {
        return Err("CODE_REVISION must be a lowercase commit hash".into());
    }
    let app = Arc::new(App {
        database_url: runtime::database_url()?,
        code_revision,
        slots: Semaphore::new(8),
        counter: AtomicU64::new(0),
        instance: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_nanos(),
    });
    let router = Router::new()
        .route("/Tabular/post.rest", post(query))
        .route("/v1/metadata", get(metadata))
        .fallback(invalid)
        .method_not_allowed_fallback(invalid)
        .layer(DefaultBodyLimit::max(128 * 1024))
        .with_state(app);
    let listener = tokio::net::TcpListener::bind(
        std::env::var("LISTEN_ADDR").unwrap_or_else(|_| "127.0.0.1:8080".into()),
    )
    .await?;
    axum::serve(listener, router)
        .with_graceful_shutdown(async {
            let mut terminate =
                tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                    .expect("install termination signal");
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {},
                _ = terminate.recv() => {},
            }
        })
        .await?;
    Ok(())
}
