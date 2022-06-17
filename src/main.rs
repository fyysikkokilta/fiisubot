use anyhow::Result;
use milli::{heed::EnvOpenOptions, Index, Search};
use serde::Deserialize;
use std::env::current_dir;
use std::fs::File;
use std::sync::{Arc, Mutex};
use teloxide::{prelude::*, types::*, utils::command::BotCommands};

#[macro_use]
extern crate lazy_static;
lazy_static! {
    //static ref BOT: AutoSend<Bot> = {
    //    Bot::from_env().auto_send()
    //};
    static ref index: Arc<Index> = {
        let mut env = EnvOpenOptions::new();
        env.map_size(10 * 1024 * 1024);

        let path = current_dir().unwrap();
        Arc::new(Index::new(env, &path).unwrap())
    };

    static ref songs: Vec<Song> = {
        serde_json::from_reader(File::open("songs.json").unwrap()).unwrap()
    };
}

#[derive(BotCommands, Clone)]
#[command(rename = "lowercase", description = "These commands are supported:")]
enum Command {
    #[command(description = "display this text.")]
    Help,
    #[command(description = "handle a username.")]
    Username(String),
    #[command(description = "handle a username and an age.", parse_with = "split")]
    UsernameAndAge { username: String, age: u8 },
}

#[derive(Deserialize, Debug)]
struct Song {
    name: String,
    melody: Option<String>,
    composer: Option<String>,
    arranger: Option<String>,
    lyrics: String,
}

#[tokio::main(flavor = "multi_thread")]
async fn main() -> Result<()> {
    let BOT = Bot::from_env().auto_send();
    println!("Bot starting with home folder {:?}", current_dir().unwrap());
    let hand_fun = |query: InlineQuery, bot: AutoSend<Bot>| async move {
        println!("Got query {:?}", query);

        let results: Vec<InlineQueryResult> = {
            let matches = match search(query.query) {
                Ok(a) => a,
                Err(e) => {
                    println!("{:?}", e);
                    vec![]
                }
            };

            matches
                .iter()
                .enumerate()
                .for_each(|(ind, song)| println!("{}: {:?}", ind, song));

            matches
                .iter()
                .enumerate()
                .map(|(ind, song)| {
                    InlineQueryResultArticle::new(
                        format!("{}", ind),
                        &song.name,
                        InputMessageContent::Text(InputMessageContentText {
                            message_text: format!("<b>{}</b>\n\n{}", &song.name, &song.lyrics),
                            parse_mode: Some(ParseMode::Html),
                            entities: None,
                            disable_web_page_preview: Some(true),
                        }),
                    )
                    .description(&song.lyrics.chars().take(100).collect::<String>())
                })
                .map(|article| InlineQueryResult::Article(article))
                .collect()
        };

        // Send it off! One thing to note -- the ID we use here must be of the query
        // we're responding to.
        let response = bot.answer_inline_query(&query.id, results).send().await;
        if let Err(err) = response {
            println!("Error in handler: {:?}", err);
        }
        respond(())
    };
    //let actual_handler =
    //    |query: InlineQuery, bot: AutoSend<Bot>| async { hand_fun(query, bot, songs.to_vec()) };

    let handler = Update::filter_inline_query().branch(dptree::endpoint(hand_fun));
    Dispatcher::builder(BOT, handler)
        .build()
        .setup_ctrlc_handler()
        .dispatch()
        .await;

    Ok(())
}


fn search(query: impl Into<String>) -> Result<Vec<&'static Song>> {
    let rtxn = index.read_txn()?;

    let matches = Search::new(&rtxn, &index)
        .query(query)
        .limit(10)
        .execute()?
        .documents_ids
        .iter()
        .flat_map(|x| usize::try_from(*x))
        .flat_map(|ind| songs.get(ind))
        .collect::<Vec<&Song>>();
    Ok(matches)
}
