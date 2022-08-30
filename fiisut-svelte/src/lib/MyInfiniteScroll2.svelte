<!--
	Child type of infinite scroll element.
	Works by having a parent that owns a IntersectionObserver
	to which a div of last 10 elements of an list is given.
	When those items become visible, a showMore() call is triggered
	deleting the current div from being watched and causing a nested
	instance of this component to be created which in turn registers
	a new div of later items to be observed.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	export let setShowMore: (fun: () => any, e: Element) => void;
	export let items: any[];
	export let loadOnNthVisible: number = 10;
	export let pageSize: number = 50;
	export let start: number = 0;
	let observed: Element;
	let showNext: boolean = false;

	const showMore = async () => {
		showNext = true;
	};
	onMount(() => {
		console.log('showing', start, start + pageSize);
		setShowMore(showMore, observed);
	});

	$: isLast = items.length <= start + pageSize;
	$: end = isLast ? items.length : start + pageSize;
	$: obsInd = isLast ? items.length : start + pageSize - loadOnNthVisible;
	$: topItems = items.slice(start, obsInd);
	$: botItems = items.slice(obsInd + 1, end);
</script>

{#each topItems as item (item.index)}
	<slot name="item" {item}>ITEM TEMPLATE MISSING</slot>
{/each}

{#if !isLast}
	<div bind:this={observed}>
		<slot name="item" item={items[obsInd]}>ITEM TEMPLATE MISSING</slot>
		{#each botItems as item (item.index)}
			<slot name="item" {item}>ITEM TEMPLATE MISSING</slot>
		{/each}
	</div>
{/if}

{#if showNext && !isLast}
	<svelte:self {items} start={start + pageSize} {setShowMore}>
		<div slot="content"><slot name="content">no content :( t recursive</slot></div>
		<div slot="item" let:item>
			<slot name="item" {item}>recursive item ata</slot>
		</div>
	</svelte:self>
{/if}
