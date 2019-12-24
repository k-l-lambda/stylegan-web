<template>
	<div class="projector"
		@paste="onPaste"
		@wheel="onWheel"
		@drop.prevent="onDropFiles"
		@dragover.prevent="drageHover = true"
		@drageleave="drageHover = false"
	>
		<aside>
			<p>
				<StoreInput v-model="projectSteps" type="number" localKey="projectorSteps" :styleObj="{width: '4em'}" :disabled="running" title="projector steps" />
				<StoreInput v-model="projectYieldInterval" type="number" localKey="projectorYieldInterval" :styleObj="{width: '4em'}" :disabled="running" title="projector yield interval" />
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
			<p v-if="focusResult">
				<a :href="focusResult.editorUrl" target="editor">Edit</a>
			</p>
		</aside>
		<article>
			<div class="target" :class="{hover: drageHover}">
				<StoreInput v-show="false" v-model="targetUrl" sessionKey="projectorTargetImageURL" />
				<img v-if="targetUrl" :src="targetUrl" />
				<span v-if="targetUrl" class="arrow">&#x1f844;</span>
				<img v-if="focusResult" :src="focusResult.img" />
			</div>
			<div class="yielding">
				<a v-for="(item, i) of reversedProjectedSequence" :key="i" class="item"
					:class="{focus: (projectedSequence.length - i - 1) === focusIndex}"
					@mouseenter="focusIndex = projectedSequence.length - i - 1"
					:href="generatorLinkFromLatents(item.latentCodes[0])"
					target="_blank"
				>
					<sup class="index">{{item.step}}.</sup>
					<img :src="item.img" />
				</a>
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
				focusIndex: 0,
				drageHover: false,
			};
		},


		computed: {
			projectProgress() {
				if (!this.projectedSequence || !this.projectedSequence.length)
					return 0;

				return this.projectedSequence[this.projectedSequence.length - 1].step;
			},


			reversedProjectedSequence() {
				return this.projectedSequence.slice().reverse();
			},


			focusResult() {
				const item = this.projectedSequence && this.projectedSequence[this.focusIndex];
				if (item)
					return {
						img: item.img,
						editorUrl: `/#psi=0.5&latents=${encodeURIComponent(item.latentCodes[0])}`,
					};

				return null;
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
					this.targetUrl = URL.createObjectURL(image.getAsFile());
				}
			},


			onWheel(event) {
				//console.log("onWheel:", event);

				this.focusIndex += event.deltaY > 0 ? -1 : 1;
				this.focusIndex = Math.max(Math.min(this.focusIndex, this.projectedSequence.length - 1), 0);
			},


			async onDropFiles(event) {
				this.drageHover = false;

				const file = event.dataTransfer.files[0];
				if (file && /^image/.test(file.type)) {
					this.targetUrl = URL.createObjectURL(file);
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
						this.focusIndex = this.projectedSequence.length - 1;
					}
				}
				catch(error) {
					console.error(error);
				}

				this.running = false;
			},


			generatorLinkFromLatents(latents, psi = 0.5) {
				return `/generate?psi=${psi}&latents=${encodeURIComponent(latents)}`;
			},
		},


		watch: {
			focusIndex() {
				const focusItem = document.querySelector(".item.focus");
				if (focusItem)
					focusItem.scrollIntoView();
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

	aside p
	{
		text-align: center;
	}

	.target
	{
		text-align: center;
		padding: 20px;
	}

	.target > *
	{
		vertical-align: middle;
	}

	.target img
	{
		max-height: 60vh;
		max-width: 30vw;
	}

	.target .arrow
	{
		font-size: 36px;
		display: inline-block;
		margin: 0 2em;
	}

	.yielding
	{
		padding: 12px 0;
		overflow-x: auto;
		white-space: nowrap;
		line-height: 260px;
	}

	.yielding .item
	{
		display: inline-block;
		line-height: normal;
		transition: .3s all;
		text-decoration: none;
		color: black;
	}

	.yielding .item .index
	{
		vertical-align: top;
	}

	.yielding .item img
	{
		width: 200px;
		vertical-align: middle;
	}

	.yielding .item.focus
	{
		transform: scale(1.1);
	}

	.yielding .item.focus img
	{
		outline: 4px solid lightgreen;
	}

	.yielding .item + .item::before
	{
		content: "\1f844";
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
		border: 1px solid #0003;
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

	div.hover
	{
		background-color: #dfd;
		outline: 1em solid lightgreen;
	}
</style>
