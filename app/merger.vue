<template>
	<div>
		<aside>
			<GView class="g-view" :layers="latentLayers" :lastDimension="latentDimension" />
			<GView class="g-view" :layers="latentLayers" :lastDimension="latentDimension" />
		</aside>
		<main>

		</main>
		<div v-show="initializing" class="initializing">Model initializing, wait a moment...</div>
	</div>
</template>

<script>
	import GView from "./g-view.vue";



	export default {
		name: "merger",


		components: {
			GView,
		},


		data () {
			return {
				spec: null,
				initializing: false,
			};
		},


		computed: {
			latentLayers () {
				return this.spec ? this.spec.synthesis_input_shape[1] : 1;
			},


			latentDimension () {
				return this.spec ? this.spec.synthesis_input_shape[2] : 512;
			},
		},


		async created () {
			window.$main = this;

			this.initializing = true;

			const res = await fetch("/spec");
			this.spec = await res.json();
			console.log("model spec:", this.spec);

			this.initializing = false;
		},
	};
</script>

<style>
	.initializing
	{
		position: absolute;
		top: 0;
		left: 0;
		bottom: 0;
		right: 0;
		font-size: 10vh;
		padding: 30vh 2em 0;
		white-space: normal;
		background-color: #ccca;
		color: #444c;
	}

	.g-view
	{
		display: inline-block;
	}
</style>
