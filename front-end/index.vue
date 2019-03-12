<template>
	<body>
		<header>
			&Psi; <input type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" :style="{width: '600px'}" /> <em class="value">{{psi}}</em>
		</header>
		<aside>
			<ul v-if="features">
				<li v-for="(feature, index) of features" :key="index">
					<input type="range" v-model.lazy="feature.normalized" :min="-1" :max="1" step="any" /> <em class="value">{{feature.value.toPrecision(4)}}</em>
				</li>
			</ul>
		</aside>
		<article>
			<img v-if="latentsBytes" :src="`/generate?psi=${psi}&latents=${latentsBytes}`" />
		</article>
	</body>
</template>

<script>
	class Feature {
		constructor (value) {
			this.value = value;
		}


		get normalized () {
			return Math.tanh(this.value);
		}


		set normalized (v) {
			this.value = Math.atanh(v);
		}
	};



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

				return btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(this.features.map(f => f.value)).buffer)));
			},
		},


		async mounted () {
			window.__main = this;

			const res = await fetch("/spec");
			const spec = await res.json();
			console.log("spec:", spec);

			Object.assign(this, spec);

			this.features = Array(spec.latents_dimensions).fill().map(() => new Feature(0));
		},
	};
</script>

<style>
	aside, article
	{
		display: inline-block;
		vertical-align: top;
	}

	.value
	{
		font-size: 9px;
	}
</style>
