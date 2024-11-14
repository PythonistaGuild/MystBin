use std::result;

use chrono::{DateTime, Utc};
use rocket_validation::Validate;
use serde::{Deserialize, Serialize};
use sqlx::{postgres::PgRow, FromRow, Row};
use validator::ValidationError;

use crate::result::{HTTPError, Result};

#[derive(Serialize)]
pub struct Position {
    line: i32,
    char: i32,
}

impl Position {
    pub fn line(&self) -> i32 {
        self.line
    }

    pub fn char(&self) -> i32 {
        self.char
    }

    pub fn new(line: i32, char: i32) -> Self {
        Position { line, char }
    }
}

#[derive(Serialize)]
pub struct Annotation {
    head: Position,
    tail: Position,
    content: String,
}

impl Annotation {
    pub fn new(head: Position, tail: Position, content: String) -> Self {
        Annotation {
            head,
            tail,
            content,
        }
    }
}

impl FromRow<'_, PgRow> for Annotation {
    fn from_row(row: &PgRow) -> std::result::Result<Self, sqlx::Error> {
        let head_line = row.get("head_line");
        let head_char = row.get("head_char");

        let tail_line = row.get("tail_line");
        let tail_char = row.get("tail_char");

        let content = row.get("content");

        let head = Position {
            line: head_line,
            char: head_char,
        };

        let tail = Position {
            line: tail_line,
            char: tail_char,
        };

        Ok(Annotation {
            head,
            tail,
            content,
        })
    }
}

#[derive(Serialize)]
pub struct File {
    name: String,
    content: String,

    lines: i32,
    characters: i32,

    annotations: Vec<Annotation>,
}

impl File {
    pub fn new(
        name: String,
        content: String,
        lines: i32,
        characters: i32,
        annotations: Vec<Annotation>,
    ) -> Self {
        File {
            name,
            content,
            lines,
            characters,
            annotations,
        }
    }
}

#[derive(Serialize)]
pub struct Paste {
    id: String,

    created_at: DateTime<Utc>,
    expires_at: Option<DateTime<Utc>>,

    views: i64,
    max_views: Option<i16>,

    files: Vec<File>,

    #[serde(skip_serializing_if = "Option::is_none")]
    security: Option<String>,
}

impl Paste {
    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn add_file(&mut self, file: File) {
        self.files.push(file);
    }

    pub fn new(
        id: String,
        created_at: DateTime<Utc>,
        expires_at: Option<DateTime<Utc>>,
        views: i64,
        max_views: Option<i16>,
        files: Vec<File>,
        security: Option<String>,
    ) -> Self {
        Paste {
            id,
            created_at,
            expires_at,
            views,
            max_views,
            files,
            security,
        }
    }
}

#[derive(Deserialize, Serialize, Validate)]
pub struct CreateFile<'r> {
    #[validate(length(min = 1, max = 32), custom(function = "validate_name"))]
    name: Option<&'r str>,
    #[validate(length(min = 1, max = 300_000))]
    // Using String instead of str because of newlines:
    // https://github.com/somehowchris/rocket-validation/issues/41
    content: String,
}

fn validate_name(name: &str) -> result::Result<(), ValidationError> {
    if !name.contains("\n") {
        Ok(())
    } else {
        Err(ValidationError::new("Newline in file name."))
    }
}

impl<'r> CreateFile<'r> {
    pub fn name(&self) -> Option<&'r str> {
        self.name
    }

    pub fn content(&self) -> &str {
        &self.content
    }
}

#[derive(Deserialize, Serialize, Validate)]
pub struct CreatePaste<'r> {
    #[validate(length(min = 1, max = 5))]
    files: Vec<CreateFile<'r>>,
    #[validate(length(min = 1, max = 72))]
    password: Option<&'r str>,
    #[validate(range(min = 1, max = 128))]
    max_views: Option<i16>,
    expires_at: Option<DateTime<Utc>>,
}

impl<'r> CreatePaste<'r> {
    pub fn files(&self) -> &'r Vec<CreateFile> {
        &self.files
    }

    pub fn password(&self) -> Option<&'r str> {
        self.password
    }

    pub fn max_views(&self) -> Option<i16> {
        self.max_views
    }

    pub fn expires_at(&self) -> Option<DateTime<Utc>> {
        self.expires_at
    }

    pub fn from_content(content: String) -> Result<Self> {
        if content.len() < 1 || content.len() > 300_000 {
            return Err(HTTPError::new(
                422,
                "Must be between 1 and 300000 in length!",
            ));
        }

        let file = CreateFile {
            name: None,
            content,
        };

        Ok(CreatePaste {
            files: vec![file],
            password: None,
            max_views: None,
            expires_at: None,
        })
    }
}
