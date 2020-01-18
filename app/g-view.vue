<template>
	<div :class="{['drage-hover']: drageHover}"
		@drop.prevent="onDropFiles"
		@dragover.prevent="drageHover = true"
		@drageleave="drageHover = false"
		@mouseleave="drageHover = false"
		@mouseup="drageHover = false"
	>
		<div class="image" :class="{loading: imageLoading}" :style="{width: `${imageSize}px`, height: `${imageSize}px`}">
			<img v-if="imageURL" :src="imageURL" @load="imageLoading = false" />
		</div>
		<div>
			<input class="hash" type="text" :value="latentsHash" :style="{width: `${imageSize - 4}px`}" :readonly="true" @paste="onPaste" @copy.prevent.stop="onCopy" />
		</div>
	</div>
</template>

<script>
	import md5 from "js-md5";
	import JSZip from "jszip";

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
			ppLatentsBytes: String,
		},


		data () {
			return {
				latents: Array(this.layers * this.lastDimension).fill(0),
				imageLoading: false,
				drageHover: false,
			};
		},


		computed: {
			latentsBytes: {
				get () {
					if (!this.latents.length)
						return null;

					return LatentCode.encodeFixed16(this.latents);
				},

				set (value) {
					this.latents = LatentCode.decodeFixed16(value);
				},
			},


			latentsHash () {
				return this.latentsBytes && md5(this.latentsBytes);
			},


			imageURL () {
				return this.latentsBytes && `/generate?fromW=1&xlatents=${encodeURIComponent(this.latentsBytes)}`;
			},
		},


		created () {
			if (this.ppLatentsBytes)
				this.latentsBytes = this.ppLatentsBytes;
		},


		methods: {
			async onPaste (event) {
				const text = await new Promise(resolve => [...event.clipboardData.items][0].getAsString(resolve));
				if (text) {
					try {
						const [_, protocol, path] = text.match(/^([\w\+]+):(.+)$/);
						switch (protocol) {
						case "w":
							const w = LatentCode.decodeFloat32(path);
							this.latents = [].concat(...Array(this.layers).fill(null).map(() => Array.from(w)));

							break;
						case "w+":
							this.latentsBytes = path;

							break;
						case "z":
							const [_, psi, bytes] = path.match(/^(.+),(.+)$/);
							const wcode = await (await fetch(`/map-z-w?psi=${psi}&z=${encodeURIComponent(bytes)}`)).text();
							const ww = LatentCode.decodeFloat32(wcode);
							this.latents = [].concat(...Array(this.layers).fill(null).map(() => Array.from(ww)));

							break;
						default:
							console.warn("invalid latent protocol:", protocol);
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


			async onDropFiles(event) {
				this.drageHover = false;

				const file = event.dataTransfer.files[0];
				if (file && /zip/.test(file.type))
					this.loadPackage(file);
			},


			async loadPackage(file) {
				const pack = await JSZip.loadAsync(file);
				const manifest = JSON.parse(await pack.file("manifest.json").async("text"));
				if (manifest.usage !== "stylegan-web-projector") {
					console.warn("unsupported package type:", manifest.usage);
					return;
				}

				console.log(`Loading package "${file.name}" with model`, manifest.model);

				if (manifest.results) {
					const lastResult = manifest.results[manifest.results.length - 1];
					if (lastResult && lastResult.xlatentCode)
						this.latentsBytes = lastResult.xlatentCode;
				}
			},
		},


		watch: {
			latents (value) {
				this.$emit("update:latents", value);
			},


			latentsBytes (value) {
				if (this.ppLatentsBytes != value)
					this.$emit("update:ppLatentsBytes", value);

				this.$emit("change", value);
			},


			ppLatentsBytes (value) {
				this.latentsBytes = value;
			},


			layers () {
				if (!this.ppLatentsBytes)
					this.latents = Array(this.layers * this.lastDimension).fill(0);
			},


			lastDimension () {
				if (!this.ppLatentsBytes)
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

	.drage-hover
	{
		background-color: #dfd;
		outline: .2em solid lightgreen;
	}
</style>
