<template>
	<div>
		<header>
			<fieldset class="vectors">
				<VectorInput /> <span class="separator">&#x2192;</span> <VectorInput />
			</fieldset>
			<fieldset>
				<StoreInput type="number" v-model.number="circlePointCount" localKey="mappingViewerCirclePointCount" title="point count" :styleObj="{width: '3em'}" />
			</fieldset>
			<fieldset>
				<button>plot</button>
			</fieldset>
		</header>
		<main>
			<!--CirclePlot :layout="plotLayout" /-->
		</main>
	</div>
</template>

<style src="./common.css"></style>
<script>
	import CirclePlot from "./circlePlot.vue";
	import VectorInput from "./vectorInput.vue";
	import StoreInput from "./storeinput.vue";



	export default {
		name: "mappingViewer",


		components: {
			CirclePlot,
			VectorInput,
			StoreInput,
		},

		
		data () {
			return {
				/*plotLayout: {
					margin: {l: 0, r: 0, t: 0, b: 0},
					width: 400,
					height: 400,
				},*/
				circlePointCount: 360,
			};
		},


		created () {
			window.$main = this;
		},
	};
</script>

<style>
	header .vectors, header .vectors > *
	{
		vertical-align: middle;
	}

	span.separator
	{
		display: inline-block;
		margin: 0 1em;
	}
</style>
