<template>
	<textarea :value="vectorText" :readonly="true" @paste="onPaste" />
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


			randomize () {
				this.vector = this.vector.map(() => LatentCode.randn_bm());
			},
		},
	};
</script>
