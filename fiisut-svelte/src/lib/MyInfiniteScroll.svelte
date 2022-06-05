<script lang="ts">
	import { onMount, tick } from 'svelte';

	let container: Element;
	let itemContainer: Element;
  // Note that items length
	export let items: any[] = [];
	export let loadOnNthVisible: number = 10;
  export let pageSize: number = 50;
  const loadOnInd = items.length > loadOnNthVisible ? loadOnNthVisible - 1 : items.length - 1
  let visible: any[] = items.splice(0, pageSize)
  let page: number = 1
  let observer: IntersectionObserver;

	console.log(items.length);
  let observed: Element;

  const showMore = async () => {
    console.log(visible);
    console.log(items, page, pageSize)
    visible = items.slice(0, (++page)*pageSize);
    console.log(items, page, pageSize)
    console.log("after", visible)
    page++;
    observer.unobserve(observed);
    await tick();
    observed = itemContainer.children[itemContainer.children.length - loadOnInd];
		observer.observe(observed);
  }

	onMount(() => {
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

    // If the index is negative the target is undefined and
    // no error is raised. That also what we want.
    observed = itemContainer.children[itemContainer.children.length - loadOnInd];
		observer.observe(observed);
	});
</script>

<div class="my-infinite-loading-container" bind:this={container}>
	<slot name="content">no content :(</slot>
	<div class="my-infinite-loading-items" bind:this={itemContainer}>
		{#each visible as item, index}
			<slot name="item" {item} {index}>ITEM TEMPLATE MISSING</slot>
		{/each}
	</div>
</div>
