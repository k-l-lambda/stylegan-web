<template>
	<header>
		<a v-for="link of links" :href="link.href" :class="{focus: link.href === pathname}">{{link.name}}</a>
	</header>
</template>

<script>
	export default {
		name: "navigator",


		data() {
			return {
				links: [
					{
						href: "/",
						name: "EXPLORER",
					},
					{
						href: "/projector/",
						name: "PROJECTOR",
					},
				],
				pathname: location.pathname,
			};
		},
	};
</script>

<style scoped>
	header
	{
		position: fixed;
		left: 0;
		top: 0;
		margin: 0;
		padding: 0 0.4em;
		font-size: 10px;
		height: unset;
		color: white;
		background: #333;
		border-bottom-right-radius: 1em;
	}

	header > a
	{
		display: inline-block;
		padding: 0 1em;
		color: inherit;
		text-decoration: none;
		border-width: 2px;
		border-color: transparent;
	}

	header > a:hover
	{
		background: #c00;
	}

	header > a.focus
	{
		border-bottom: 2px solid white;
		font-weight: bold;
	}
</style>
