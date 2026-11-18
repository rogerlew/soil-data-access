use serde::Deserialize;
use sqlparser::{
    ast::{Expr, InTarget, SetExpr, Statement, Value},
    dialect::MsSqlDialect,
    parser::Parser,
};
use std::sync::OnceLock;

#[derive(Deserialize)]
pub struct Family {
    pub family: String,
    pub template: String,
    pub columns: Vec<String>,
    pub postgres_sql: String,
}

pub struct Plan {
    pub family: &'static Family,
    pub keys: Vec<i64>,
}

pub fn catalog() -> &'static [Family] {
    static CATALOG: OnceLock<Vec<Family>> = OnceLock::new();
    CATALOG.get_or_init(|| {
        serde_json::from_str(include_str!("../contracts/runtime-query-catalog.json"))
            .expect("compiled catalog")
    })
}

fn shape(sql: &str) -> Result<(String, Vec<i64>), ()> {
    if sql.len() > 65536 {
        return Err(());
    }
    let mut statements = Parser::new(&MsSqlDialect {})
        .with_recursion_limit(64)
        .try_with_sql(sql)
        .map_err(|_| ())?
        .parse_statements()
        .map_err(|_| ())?;
    if statements.len() != 1 {
        return Err(());
    }
    let Statement::Query(query) = &mut statements[0] else {
        return Err(());
    };
    let SetExpr::Select(select) = query.body.as_mut() else {
        return Err(());
    };
    let Some(Expr::In {
        target: InTarget::List(list),
        negated: false,
        ..
    }) = select.selection.as_mut()
    else {
        return Err(());
    };
    if list.is_empty() || list.len() > 4096 {
        return Err(());
    }
    let keys = list
        .iter()
        .map(|expr| {
            let Expr::Value(value) = expr else {
                return Err(());
            };
            let text = match &value.value {
                Value::Number(text, false) | Value::SingleQuotedString(text) => text,
                _ => return Err(()),
            };
            if text.is_empty() || !text.bytes().all(|b| b.is_ascii_digit()) {
                return Err(());
            }
            text.parse::<i64>().map_err(|_| ())
        })
        .collect::<Result<Vec<_>, _>>()?;
    *list = vec![Expr::Value(Value::Number("1".into(), false).into())];
    // Rendering is only a shape fingerprint. It is NEVER sent to PostgreSQL.
    Ok((statements[0].to_string().to_ascii_lowercase(), keys))
}

pub fn admit(sql: &str) -> Result<Plan, ()> {
    let (fingerprint, keys) = shape(sql)?;
    for family in catalog() {
        if fingerprint == shape(&family.template)?.0 {
            return Ok(Plan { family, keys });
        }
    }
    Err(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn accepts_frozen_families_and_exact_large_keys() {
        for family in catalog() {
            let sql = family
                .template
                .to_lowercase()
                .replace("1001,1002", "'9007199254740993',0002");
            let plan = admit(&sql).unwrap();
            assert_eq!(plan.keys, vec![9007199254740993, 2]);
            assert!(!plan.family.postgres_sql.contains("9007199254740993"));
        }
    }
    #[test]
    fn rejects_unowned_shapes_and_literals() {
        let query = &catalog()[2].template;
        for sql in [
            format!("{query}; SELECT 1"),
            query.replace("fragvol_r", "pg_sleep(10)"),
            query.replace("1001,1002", "1) OR 1=1 --"),
            query.replace("1001,1002", "-1"),
            query.replace("1001,1002", "1.5"),
            query.replace("1001,1002", "9223372036854775808"),
            query.replace("chfrags", "pg_catalog.pg_authid"),
            format!("{query} DESC"),
            query.replace(" IN ", " NOT IN "),
            query.replace("1001,1002", "SELECT 1"),
            query.replace("1001,1002", "'1;DROP TABLE component'"),
            query.replace("SELECT", "SELECT TOP 1"),
            query.replace("chkey,", "chkey AS hidden,"),
            query.replace("1001,1002", &vec!["1"; 4097].join(",")),
        ] {
            assert!(admit(&sql).is_err(), "{sql}");
        }
    }
}
