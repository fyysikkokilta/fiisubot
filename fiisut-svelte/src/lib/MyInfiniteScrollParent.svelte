<script context="module">
	import MyInfiniteScroll from './MyInfiniteScroll2.svelte';
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	let observer: IntersectionObserver;
	if (typeof window !== 'undefined')
		observer = new IntersectionObserver(
			async (entries) => {
				console.log(entries);
				if (entries[0].isIntersecting === true) {
					await showMore();
					console.log('element visible :D');
				}
			},
			{ threshold: [0] }
		);

	export let items: any[];

	let showMore: () => void;
	let observed: Element | undefined = undefined;
	const setShowMore = (fun: () => void, toObserve: Element | undefined) => {
		showMore = fun;
		if (observed !== undefined) observer.unobserve(observed);
		if (toObserve !== undefined)
			// undefined toObserve means last page is viewed
			observer.observe(toObserve);
		observed = toObserve;
	};
	onMount(() => {
		console.log('Parent mounted');
	});
</script>

<MyInfiniteScroll {items} {setShowMore}>
	<div slot="content"><slot name="content">no content :( t parent</slot></div>
	<div slot="item" let:item><slot name="item" {item}>parent item ata</slot></div>
</MyInfiniteScroll>
