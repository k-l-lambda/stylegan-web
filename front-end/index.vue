<template>
	<body>
		<img v-if="latentsBytes" :src="`/generate?psi=${psi}&latents=${latentsBytes}`" />
	</body>
</template>

<script>
	export default {
		name: "index",


		data () {
			return {
				model: null,
				latents_dimensions: null,
				features: null,
				psi: 0.7,
			};
		},


		computed: {
			latentsBytes () {
				if (!this.features)
					return null;

				return btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(this.features).buffer)));
			},
		},


		async mounted () {
			window.__main = this;

			const res = await fetch("/spec");
			const spec = await res.json();
			console.log("spec:", spec);

			Object.assign(this, spec);

			this.features = Array(spec.latents_dimensions).fill(0);
		},
	};
</script>

<style>

</style>
