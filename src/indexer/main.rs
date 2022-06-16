use anyhow::Result;
use milli::{
    documents::{DocumentBatchReader},
    heed::EnvOpenOptions,
    update::{IndexDocuments, IndexDocumentsConfig, IndexerConfig, self},
    Index,
};
use std::fs::File;
use std::{
    env::current_dir,
    io::{Cursor, Read},
};
use serde_json::{
    Value, Map, Number
};

fn main() -> Result<()> {
    let path = current_dir()?;
    let mut options = EnvOpenOptions::new();
    options.map_size(10 * 1024 * 1024);
    let index = Index::new(options, &path)?;
    let mut txn = index.write_txn()?;

    let reader = DocumentBatchReader::from_reader(Cursor::new(documents_from_json(File::open(
        path.join("documents.json"),
    )?)?))?;


    let config = IndexerConfig::default();
    let indexing_config = IndexDocumentsConfig::default();


    let builder = update::Settings::new(&mut txn, &index, &config);
    //builder.set_primary_key("name".to_string());
    builder.execute(|_| ())?;

    let mut addition =
        IndexDocuments::new(&mut txn, &index, &config, indexing_config.clone(), |_| ())?;

    addition.add_documents(reader)?;
    addition.execute()?;
    txn.commit()?;
    println!("Hello, indexer!");
    Ok(())
}



fn documents_from_json(reader: impl Read) -> Result<Vec<u8>> {
    let mut writer = Cursor::new(Vec::new());
    let mut documents = milli::documents::DocumentBatchBuilder::new(&mut writer)?;

    let mut de: Vec<Map<String, Value>> = serde_json::from_reader(reader)?;
    de.iter_mut().enumerate().for_each(|(pos, it)| {
        let val =  Value::Number(Number::from(pos));
        it.insert("id".to_string(), val);
    });

    documents.extend_from_json(serde_json::to_string(&de)?.as_bytes())?;
    documents.finish()?;

    Ok(writer.into_inner())
}
