<template>
	<div @paste="onPaste" class="projector">
		<aside>
			<p>
				<StoreInput v-model="projectSteps" localKey="projectorSteps" :styleObj="{width: '4em'}" :disabled="running" title="projector steps" />
				<StoreInput v-model="projectYieldInterval" localKey="projectorYieldInterval" :styleObj="{width: '4em'}" :disabled="running" title="projector yield interval" />
			</p>
			<p>
				<button :disabled="running" @click="project">Project</button>
			</p>
			<p>
				<span class="progress-bar">
					<span class="fill" :style="{width: `${(projectProgress / projectSteps) * 100}%`}"></span>
					<span class="desc" v-if="running">
						{{projectProgress}} / {{projectSteps}}
					</span>
				</span>
			</p>
		</aside>
		<article>
			<div class="target">
				<StoreInput v-show="false" v-model="targetUrl" sessionKey="projectorTargetImageURL" />
				<img v-if="targetUrl" :src="targetUrl" />
			</div>
			<div class="yielding">
				<span v-for="(item, i) of projectedSequence" :key="i" class="item">
					<sup class="index">{{item.step}}.</sup>
					<img :src="item.img" />
				</span>
			</div>
		</article>
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

		const SEPARATOR = "\n\n";
		let textBuffer = "";
		const yieldSegment = () => {
			const si = textBuffer.indexOf(SEPARATOR);
			if (si >= 0) {
				const result = textBuffer.substr(0, si);
				textBuffer = textBuffer.substr(si + SEPARATOR.length);

				return result;
			}
		};

		const reader = response.body.getReader();
		while (true) {
			const {done, value} = await reader.read();
			//console.log("read:", done, value);
			if (value) {
				textBuffer += Array.from(value).map(b => String.fromCharCode(b)).join("");

				while(true) {
					const segment = yieldSegment();
					if (segment)
						yield JSON.parse(segment);
					else
						break;
				}
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
				projectedSequence: [],
				projectSteps: 200,
				projectYieldInterval: 10,
				running: false,
			};
		},


		computed: {
			projectProgress() {
				if (!this.projectedSequence || !this.projectedSequence.length)
					return 0;

				return this.projectedSequence[this.projectedSequence.length - 1].step;
			},
		},


		created() {
			window.$main = this;
		},


		methods: {
			async onPaste(event) {
				//console.log("onPaste:", event);

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
					console.warn("target image is null.");
					return;
				}

				this.running = true;
				this.projectedSequence = [];

				try {
					for await (const result of projectImage(target, {steps: this.projectSteps, yieldInterval: this.projectYieldInterval})) {
						//console.log("project value:", value);
						this.projectedSequence.push(result);
					}
				}
				catch(error) {
					console.error(error);
				}

				this.running = false;
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

	aside
	{
		float: right;
		position: relative;
		padding: 2em;
	}

	.target
	{
		text-align: center;
	}

	.target img
	{
		max-height: 60vh;
	}

	.yielding
	{
		padding: 12px 0;
		overflow-x: auto;
		white-space: nowrap;
	}

	.yielding .item .index
	{
		vertical-align: top;
	}

	.yielding .item img
	{
		max-width: 200px;
		vertical-align: middle;
	}

	.yielding .item + .item::before
	{
		content: "\2b95";
		vertical-align: middle;
		display: inline-block;
		margin-left: 1em;
	}

	.progress-bar
	{
		position: relative;
		display: inline-block;
		width: 100%;
		height: 1.2em;
		text-align: center;
		border: 1px solid #000a;
	}

	.progress-bar .fill
	{
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		background: steelblue;
		z-index: -1;
	}

	.progress-bar .desc
	{
		text-shadow: 1px 1px 1px #fffc;
	}
</style>
