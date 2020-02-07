<template>
	<div>
	</div>
</template>

<script>
	//import {randn_bm} from "./latentCode.js";



	export default {
		name: "circle-plot",


		props: {
			layout: {
				type: Object,
				default: () => ({
					width: 1200,
					height: 800,
				}),
			},
			center: Float32Array,
			circle: Array,
			mode: {
				type: String,
				default: "3d",
			},
		},


		/*data () {
			return {
				normal: this.center.map(() => randn_bm()),
			};
		},*/


		computed: {
			normalPoints () {
				if (!this.circle)
					return null;

				return this.circle.map(p => {
					const v = Array.from(p).map((x, i) => x - this.center[i]);

					return v;
				});
			},
		},


		created () {
			console.assert(window.Plotly, "plotly is required.");
		},


		mounted () {
			this.updatePlot();
		},


		methods: {
			updatePlot () {
				const points = [...this.normalPoints, this.normalPoints[0]];	// close the cycle
				const color = points.map((_, i) => i);
				const marker = {
					size: 3.5,
					color,
					colorscale: "Greens",
					cmin: -20,
					cmax: 50,
				};

				const data = this.mode === "2d" ? Array(256).fill().map((_, i) => ({
					type: "scatter3d",
					mode: "lines+markers",
					x: points.map(v => v[i * 2]),
					y: points.map(v => v[i * 2 + 1]),
					z: points.map(_ => 0),
					line: {
						width: 6,
						color,
						//colorscale: "Viridis",
					},
					marker,
				}))
				: Array(170).fill().map((_, i) => ({
					type: "scatter3d",
					mode: "lines+markers",
					x: points.map(v => v[i * 3]),
					y: points.map(v => v[i * 3 + 1]),
					z: points.map(v => v[i * 3 + 2]),
					line: {
						width: 6,
						color,
						//colorscale: "Viridis",
					},
					marker,
				}))

				Plotly.newPlot(this.$el, data, {
					margin: {l: 0, r: 0, t: 0, b: 0},
					...this.layout,
				});
			},
		},


		watch: {
			normalPoints: "updatePlot",
		},
	};
</script>
