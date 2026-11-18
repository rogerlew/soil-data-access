// Local container configuration and bounded readiness; never report credentials.
use std::{
    io::{Read, Write},
    net::{SocketAddr, TcpStream},
    time::{Duration, Instant},
};

pub fn database_url() -> Result<String, Box<dyn std::error::Error>> {
    let direct = std::env::var_os("DATABASE_URL");
    let file = std::env::var_os("DATABASE_URL_FILE");
    let value = match (direct, file) {
        (Some(value), None) => value.into_string().map_err(|_| "Invalid DATABASE_URL")?,
        (None, Some(path)) => std::fs::read_to_string(path)
            .map_err(|_| "Cannot read DATABASE_URL_FILE")?
            .trim()
            .to_owned(),
        _ => return Err("Set exactly one of DATABASE_URL and DATABASE_URL_FILE".into()),
    };
    if value.is_empty() {
        return Err("Empty database configuration".into());
    }
    Ok(value)
}

fn remaining(deadline: Instant) -> std::io::Result<Duration> {
    deadline
        .checked_duration_since(Instant::now())
        .filter(|value| !value.is_zero())
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::TimedOut, "readiness deadline"))
}

pub fn probe(address: SocketAddr, release: Option<&str>, budget: Duration) -> Result<(), ()> {
    let deadline = Instant::now() + budget;
    let mut stream = TcpStream::connect_timeout(&address, budget).map_err(|_| ())?;
    stream
        .set_write_timeout(Some(remaining(deadline).map_err(|_| ())?))
        .map_err(|_| ())?;
    stream
        .write_all(b"GET /v1/metadata HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        .map_err(|_| ())?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 4096];
    loop {
        stream
            .set_read_timeout(Some(remaining(deadline).map_err(|_| ())?))
            .map_err(|_| ())?;
        let count = stream.read(&mut buffer).map_err(|_| ())?;
        if count == 0 {
            break;
        }
        if bytes.len() + count > 65536 {
            return Err(());
        }
        bytes.extend_from_slice(&buffer[..count]);
    }
    let boundary = bytes
        .windows(4)
        .position(|part| part == b"\r\n\r\n")
        .ok_or(())?;
    let headers = std::str::from_utf8(&bytes[..boundary]).map_err(|_| ())?;
    if !matches!(
        headers.lines().next(),
        Some("HTTP/1.0 200 OK" | "HTTP/1.1 200 OK")
    ) {
        return Err(());
    }
    let body: serde_json::Value = serde_json::from_slice(&bytes[boundary + 4..]).map_err(|_| ())?;
    if body["ready"] != true {
        return Err(());
    }
    if let Some(expected) = release {
        if body["active_release"]["id"].as_str() != Some(expected) {
            return Err(());
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::TcpListener;
    fn response(body: &'static str, expected: Option<&str>) -> Result<(), ()> {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let task = std::thread::spawn(move || {
            let (mut socket, _) = listener.accept().unwrap();
            let mut request = [0; 1024];
            socket.read(&mut request).unwrap();
            write!(
                socket,
                "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n{}",
                body.len(),
                body
            )
            .unwrap();
        });
        let result = probe(address, expected, Duration::from_secs(1));
        task.join().unwrap();
        result
    }
    #[test]
    fn checks_active_release_and_readiness() {
        assert!(response(r#"{"ready":true,"active_release":{"id":"r1"}}"#, Some("r1")).is_ok());
        assert!(response(r#"{"ready":true,"active_release":{"id":"r1"}}"#, Some("r2")).is_err());
        assert!(response(r#"{"ready":false}"#, None).is_err());
        assert!(response("invalid", None).is_err());
    }
    #[test]
    fn bounds_stalled_headers() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let task = std::thread::spawn(move || {
            let (_socket, _) = listener.accept().unwrap();
            std::thread::sleep(Duration::from_millis(200));
        });
        let start = Instant::now();
        assert!(probe(address, None, Duration::from_millis(50)).is_err());
        assert!(start.elapsed() < Duration::from_millis(180));
        task.join().unwrap();
    }
}
