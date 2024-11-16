use rocket::{
    get,
    response::content::{RawHtml, RawJson},
};
use scalar_doc::{Documentation, Theme};

#[get("/docs")]
pub fn get_docs() -> RawHtml<String> {
    let docs = Documentation::new("MystBin API Documentation", "/docs/spec.json")
        .theme(Theme::Alternate)
        .build()
        .unwrap();

    RawHtml(docs)
}

#[get("/docs/spec.json")]
pub fn get_spec() -> RawJson<&'static str> {
    RawJson(include_str!("../../openapi.json"))
}
