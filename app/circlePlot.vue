<template>
	<div>
	</div>
</template>

<script>
	export default {
		name: "mappingViewer",


		props: {
			layout: {
				type: Object,
				default: () => ({
					width: 400,
					height: 400,
				}),
			},
		},


		created () {
			console.assert(window.Plotly, "plotly is required.");
		},


		mounted () {
			const pointCount = 31;

			const x = [];
			const y = [];
			const z = [];
			const c = [];

			for (let i = 0; i < pointCount; i++) {
				const r = 10 * Math.cos(i / 10);
				x.push(r * Math.cos(i));
				y.push(r * Math.sin(i));
				z.push(i);
				c.push(i);
			}

			Plotly.newPlot(this.$el, [
				{
					type: "scatter3d",
					mode: "lines+markers",
					x: x,
					y: y,
					z: z,
					line: {
						width: 6,
						color: c,
						//colorscale: "Viridis"
					},
					marker: {
						size: 3.5,
						color: c,
						colorscale: "Greens",
						cmin: -20,
						cmax: 50,
					},
				}
			], {
				margin: {l: 0, r: 0, t: 0, b: 0},
				...this.layout,
			});
		}
	};
</script>
