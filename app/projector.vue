<template>
	<div @paste="onPaste" class="projector">
		<StoreInput v-show="false" v-model="targetUrl" sessionKey="projectorTargetImageURL" />
		<img v-if="targetUrl" :src="targetUrl" />
	</div>
</template>

<script>
	import StoreInput from "./storeinput.vue";



	const projectImage = async function* (image, {path = "/project", steps = 200, yieldInterval = 10}) {
		const form = new FormData();
		form.append("image", image);

		const response = await fetch(`${path}?steps=${steps}&yieldInterval=${yieldInterval}`, {
			method: "POST",
			body: form,
		});
		if (!response.ok) {
			console.warn("project fetch failed:", await response.text());
			throw new Error("project fetch failed");
		}
		const reader = response.body.getReader();
		while (true) {
			const {done, value} = await reader.read();
			//console.log("read:", done, value);
			if (value) {
				const text = Array.from(value).map(b => String.fromCharCode(b)).join("");

				// TODO: yield when read separator
				yield JSON.parse(text);
			}
			if (done)
				break;
		}
	};



	export default {
		name: "projector",


		components: {
			StoreInput,
		},


		data() {
			return {
				targetUrl: null,
			};
		},


		created() {
			window.$main = this;
		},


		methods: {
			async onPaste(event) {
				console.log("onPaste:", event);

				const image = [...event.clipboardData.items].filter(item => item.type.match(/image/))[0];
				if (image) {
					//console.log("image:", image.getAsFile());
					const buffer = await new Promise(resolve => {
						const reader = new FileReader();
						reader.onload = event => resolve(event.target.result);
						reader.readAsArrayBuffer(image.getAsFile());
					});
					this.targetUrl = URL.createObjectURL(new Blob([buffer], {type: image.type}));
				}
			},


			async project() {
				const url = this.targetUrl;
				const response = await fetch(url);
				const target = await response.blob();
				if (!target) {
					console.warn("target image is null");
					return;
				}

				for await (const value of projectImage(target, {steps: 5, yieldInterval: 1})) {
					console.log("project value:", value);
				}
			},
		},
	};
</script>

<style>
	body
	{
		position: absolute;
		width: 100%;
		height: 100%;
		margin: 0;
	}

	.projector
	{
		position: absolute;
		width: 100%;
		height: 100%;
	}
</style>
