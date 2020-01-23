<template>
	<span class="vector-input">
		<textarea :value="vectorText" :readonly="true" @paste="onPaste" @copy.prevent="onCopy" :class="{'note-box': true, activated}" />
		<button @click="randomize" class="icon" title="randomize">&#x1f3b2;</button>
	</span>
</template>

<script>
	import * as LatentCode from "./latentCode.js"



	export default {
		name: "vector-input",


		props: {
			dimension: {
				type: Number,
				default: 512,
			},
		},


		data () {
			return {
				vector: new Float32Array(this.dimension),
				activated: false,
			};
		},


		computed: {
			vectorText () {
				return Array.from(this.vector).map(v => v.toPrecision(4)).join(",");
			},


			latentsBytes: {
				get () {
					return LatentCode.encodeFloat32(this.vector);
				},

				set (value) {
					this.vector = LatentCode.decodeFloat32(value);
				},
			},
		},


		created () {
			this.randomize();
		},


		methods: {
			async onPaste (event) {
				const text = await new Promise(resolve => [...event.clipboardData.items][0].getAsString(resolve));
				//console.log("pasted:", text);
				const [code] = text.match(/[^,]+$/);
				this.latentsBytes = code;
			},


			onCopy () {
				event.clipboardData.setData("text/plain", "z:1," + this.latentsBytes);
				console.log("Latent code copied into clipboard.");

				this.activated = true;
				setTimeout(() => this.activated = false, 100);
			},


			randomize () {
				this.vector = this.vector.map(() => LatentCode.randn_bm());
			},
		},
	};
</script>

<style src="./common.css"></style>
<style scoped>
	.vector-input > *
	{
		vertical-align: middle;
	}
</style>
