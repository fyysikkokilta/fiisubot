<script lang="ts">
	import MyInfiniteScroll from '$lib/MyInfiniteScrollParent.svelte';
	import _allSongs from '$lib/lauluwiki.json';
	import allSongs_idx from '$lib/lauluwiki_lunr_idx';
	import lunr from 'lunr';
	import lunr_stemmer from 'lunr-languages/lunr.stemmer.support.js';
	//import lunr_fi from 'lunr-languages/lunr.fi.js';
	import lunr_sv from 'lunr-languages/lunr.sv.js';
	//import lunr_multi from 'lunr-languages/lunr.multi.js';

	lunr_stemmer(lunr)
	//lunr_fi(lunr)
	lunr_sv(lunr)
	//lunr_multi(lunr)
	const idx = lunr.Index.load(allSongs_idx)

	//import _allSongs from '$lib/songs.json';
	let searchTerm = '';
	const allSongs = _allSongs.map((e, i) => ({ ...e, index: i }));

	let shownSongs = allSongs;
	const getSongs = (searchTerm: str) => {
		try{
			return idx.search(searchTerm).map(e => allSongs[parseInt(e.ref)])
		} catch (e) {
			if (e instanceof lunr.QueryParseError) {
				return shownSongs
			}
			throw e;
		}
	}
	$: shownSongs = getSongs(searchTerm)
</script>

<div id="app">
	<header class="hacker-news-header">
		<a target="_blank" href="http://www.ycombinator.com/">
			<img src="https://fyysikkokilta.fi/favicon.ico" alt="Logo" />
		</a>
		<span>Fiisut</span>
		<input bind:value={searchTerm}

		/>
		<!-- <select bind:value={newsType} on:change={changeType}>
			<option value="story">Story</option>
			<option value="poll">Poll</option>
			<option value="show_hn">Show hn</option>
			<option value="ask_hn">Ask hn</option>
			<option value="front_page">Front page</option>
		</select> -->
	</header>

	<MyInfiniteScroll items={shownSongs}>
		<div slot="content">cont div</div>
		<div slot="item" let:item>
			{#if item}
			<div class="hacker-news-item" data-num={item.index + 1}>
				<p class="song-name">{item.index} {item.name}</p>
				<p class="song">
					{@html item.lyrics}
				</p>
			</div>
			{/if}
		</div>
	</MyInfiniteScroll>
	<!-- <InfiniteLoading on:infinite={infiniteHandler} identifier={infiniteId}>
    <div slot="noMore" style="display: none;"></div>
  </InfiniteLoading> -->
</div>

<style>
	:global(body) {
		padding-top: 28px;
		background-color: #f6f6ef;
	}
	.song {
		white-space: pre-wrap;
	}
	.hacker-news-header {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		padding: 4px 20px;
		line-height: 14px;
		background-color: #343a40;
	}
	.hacker-news-header img {
		border: 1px solid #fff;
		vertical-align: middle;
	}
	.hacker-news-header span {
		font-family: Verdana, Geneva, sans-serif;
		font-size: 14px;
		font-weight: bold;
		vertical-align: middle;
		color: #f8f9fa;
	}
	.hacker-news-header select {
		float: right;
		color: #fff;
		background-color: transparent;
		border: 1px solid #fff;
		outline: none;
		padding: 0;
		margin: 0;
	}
	.hacker-news-item {
		margin: 10px 0;
		padding: 0 10px 0 40px;
		line-height: 16px;
		font-size: 14px;
	}
	.hacker-news-item::before {
		content: attr(data-num) '.';
		float: left;
		margin-left: -40px;
		width: 32px;
		color: #888;
		text-align: right;
		font-size: 10px;
	}
	.hacker-news-item p {
		margin: 0;
		font-size: 12px;
	}
	.hacker-news-item p,
	.hacker-news-item p {
		color: #111;
	}
	.hacker-news-item p a:not(:hover) {
		text-decoration: none;
	}
	.hacker-news-item > .song-name {
		font-weight: bold;
		padding-bottom: 5px;
		margin-top: 10px;
	}
</style>
