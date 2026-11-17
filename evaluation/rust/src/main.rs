use serde_json::{json, Value};
use sqlparser::{dialect::MsSqlDialect, parser::Parser};
use std::{env, fs};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = env::args().nth(1).ok_or("expected corpus path")?;
    let corpus: Vec<Value> = serde_json::from_str(&fs::read_to_string(path)?)?;
    let mut results = Vec::new();
    for case in corpus {
        let sql = case["sql"].as_str().ok_or("sql must be a string")?;
        let result = match Parser::parse_sql(&MsSqlDialect {}, sql) {
            Ok(statements) => json!({"id":case["id"],"category":case["category"],"parsed":true,
                "statement_count":statements.len(),"rendered":statements.iter().map(ToString::to_string).collect::<Vec<_>>()}),
            Err(error) => {
                json!({"id":case["id"],"category":case["category"],"parsed":false,"error":error.to_string()})
            }
        };
        results.push(result);
    }
    println!("{}", serde_json::to_string_pretty(&results)?);
    Ok(())
}
