<template>
	<div>
		<div class="image" :class="{loading: imageLoading}" :style="{width: `${imageSize}px`, height: `${imageSize}px`}">
			<img v-if="imageURL" :src="imageURL" @load="imageLoading = false" />
		</div>
		<div>
			<input class="hash" type="text" :value="latentsHash" :style="{width: `${imageSize - 4}px`}" :readonly="true" @paste="onPaste" @copy.prevent="onCopy" />
		</div>
	</div>
</template>

<script>
	import md5 from "js-md5";

	import * as LatentCode from "./latentCode.js"



	export default {
		name: "GView",


		props: {
			layers: Number,
			lastDimension: {
				type: Number,
				default: 512,
			},
			imageSize: {
				type: Number,
				default: 200,
			},
		},


		data () {
			return {
				latents: Array(this.layers * this.lastDimension).fill(0),
				imageLoading: false,
			};
		},


		computed: {
			latentsBytes: {
				get () {
					return LatentCode.encodeFixed16(this.latents);
				},

				set (value) {
					this.latents = LatentCode.decodeFixed16(value);
				},
			},


			latentsHash () {
				return md5(this.latentsBytes);
			},


			imageURL () {
				return `/generate?fromW=1&xlatents=${encodeURIComponent(this.latentsBytes)}`;
			},
		},


		methods: {
			async onPaste (event) {
				const text = await new Promise(resolve => [...event.clipboardData.items][0].getAsString(resolve));
				if (text) {
					try {
						const [_, protocol, path] = text.match(/^([\w\+]+):(.+)$/);
						switch (protocol) {
						case "w":
							// TODO:

							break;
						case "w+":
							this.latentsBytes = path;

							break;
						default:
							console.warn("only w, w+ protocol supported.");
						}
					}
					catch (error) {
						console.warn("invalid latent URL:", error);
					}
				}
			},


			onCopy (event) {
				event.clipboardData.setData("text/plain", "w+:" + this.latentsBytes);
				console.log("Latent code copied into clipboard.");
			},
		},


		watch: {
			latents (value) {
				this.$emit("update:latents", value);
			},


			latentsBytes (value) {
				this.$emit("update:latentsBytes", value);
			},


			layers () {
				this.latents = Array(this.layers * this.lastDimension).fill(0);
			},


			lastDimension () {
				this.latents = Array(this.layers * this.lastDimension).fill(0);
			},


			imageURL () {
				this.imageLoading = true;
			},
		},
	};
</script>

<style scoped>
	.image
	{
		position: relative;
	}

	.image img
	{
		width: 100%;
		height: 100%;
	}

	.loading img
	{
		opacity: 0.7;
	}

	.hash
	{
		color: #0006;
	}

	.hash:focus
	{
		color: #000;
	}
</style>
