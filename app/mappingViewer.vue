<template>
	<div>
		<div ref="plot">
		</div>
	</div>
</template>

<script>
	export default {
		name: "mappingViewer",

		created () {
			//console.log("plotly:", plotly);
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

			Plotly.newPlot(this.$refs.plot, [
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
				width: 400,
				height: 400,
			});
		}
	};
</script>
