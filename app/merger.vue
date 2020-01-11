<template>
	<div class="merger">
		<aside>
			<p>
				<GView class="g-view" :layers="latentLayers" :lastDimension="latentDimension" :latents.sync="sourceLatents[0]" @change="updateResultLatents" />
				<GView class="g-view" :layers="latentLayers" :lastDimension="latentDimension" :latents.sync="sourceLatents[1]" @change="updateResultLatents" />
			</p>
			<table class="turner">
				<tbody>
					<tr v-for="bar of bars" :key="bar.index">
						<td>
							<input type="checkbox" v-model="bar.chosen" />
						</td>
						<td class="index">
							{{bar.index + 1}}.
						</td>
						<td class="slider">
							<input type="range" v-model.number="bar.value" :min="-1" :max="1" step="any" @change="updateResultLatentsLayer(bar.index)" />
						</td>
						<td class="value">
							{{bar.value.toFixed(2)}}
						</td>
					</tr>
				</tbody>
			</table>
		</aside>
		<main>
			<img v-if="resultImageURL" :src="resultImageURL" />
		</main>
		<div v-show="initializing" class="initializing">Model initializing, wait a moment...</div>
	</div>
</template>

<script>
	import Vue from "vue";

	import GView from "./g-view.vue";

	import * as LatentCode from "./latentCode.js"



	export default {
		name: "merger",


		components: {
			GView,
		},


		data () {
			return {
				spec: null,
				initializing: false,
				bars: [],
				sourceLatents: [null, null],
				resultLatents: null,
			};
		},


		computed: {
			latentLayers () {
				return this.spec ? this.spec.synthesis_input_shape[1] : 0;
			},


			latentDimension () {
				return this.spec ? this.spec.synthesis_input_shape[2] : 512;
			},


			/*resultLatents () {
				return this.bars.map((k, i) => (this.sourceLatents[0][i] * (1 - k) + this.sourceLatents[1][i] * (k + 1)) / 2);
			},*/


			resultLatentsBytes () {
				return this.resultLatents && LatentCode.encodeFixed16(this.resultLatents);
			},


			resultImageURL () {
				return this.resultLatentsBytes && `/generate?fromW=1&xlatents=${encodeURIComponent(this.resultLatentsBytes)}`;
			},
		},


		async created () {
			window.$main = this;

			this.initializing = true;

			const res = await fetch("/spec");
			this.spec = await res.json();
			console.log("model spec:", this.spec);

			this.resultLatents = Array(this.spec.synthesis_input_shape[1] * this.spec.synthesis_input_shape[2]).fill(0);

			this.initializing = false;
		},


		methods: {
			updateResultLatentsLayer (layer) {
				if (!this.resultLatents || !this.sourceLatents[0] || !this.sourceLatents[1])
					return;

				const k = this.bars[layer].value;
				for (let i = 0; i < this.latentDimension; ++i) {
					const index = layer * this.latentDimension + i;
					//this.resultLatents[index] = (this.sourceLatents[0][index] * (1 - k) + this.sourceLatents[1][index] * (k + 1)) / 2;
					Vue.set(this.resultLatents, index, (this.sourceLatents[0][index] * (1 - k) + this.sourceLatents[1][index] * (k + 1)) / 2);
				}
			},


			updateResultLatents () {
				for (let i = 0; i < this.latentLayers; ++i)
					this.updateResultLatentsLayer(i);
			},
		},


		watch: {
			latentLayers () {
				this.bars = Array(this.latentLayers).fill(null).map((_, i) => ({
					index: i,
					chosen: true,
					value: 0,
				}));

				this.updateResultLatents();
			},
		},
	};
</script>

<style>
	.initializing
	{
		position: fixed;
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

	.turner .index
	{
		font-size: 10px;
	}

	.turner .slider input
	{
		width: 320px;
	}

	body
	{
		overflow: hidden;
	}

	.merger
	{
		position: relative;
	}

	main
	{
		position: absolute;
		left: 420px;
		top: 0;
	}
</style>
