<template>
	<div class="projector"
		@paste="onPaste"
		@wheel="onWheel"
		@drop.prevent="onDropFiles"
		@dragover.prevent="drageHover = true"
		@drageleave="drageHover = false"
		@mouseup="drageHover = false"
	>
		<aside>
			<p>
				<StoreInput v-model="projectSteps" type="number" localKey="projectorSteps" :styleObj="{width: '4em'}" :disabled="running" title="projector steps" />
				/
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
				<a :href="!running && focusResult.editorUrl" target="editor"><span v-show="!running">Explore </span>#{{focusResult.step}}</a>
				<button @click="copyLatentCode" title="copy latent code">&#x2398;</button>
			</p>
			<p>
				<input type="text" v-model="targetName" placeholder="target name" :style="{width: '8em'}" />
				<button title="save target &amp; result" class="icon" @click="save" :disabled="!focusResult">&#x1f4be;</button>
				<button @click="showAnimationPanel = true" :disabled="!projectedSequence.length">GIF</button>
			</p>
			<p v-show="projectedSequence.length > 0">
				<!--StoreInput type="checkbox" v-model="showAll" sessionKey="projectorShowAllSequenceItems" />show all-->
				<input type="checkbox" v-model="showAll" />show all
			</p>
		</aside>
		<main>
			<div class="target" :class="{hover: drageHover}">
				<StoreInput v-show="false" v-model="targetUrl" sessionKey="projectorTargetImageURL" />
				<StoreInput v-show="false" v-model="targetName" sessionKey="projectorTargetName" />
				<div v-if="!targetUrl" class="placeholder">
					<strong>DROP</strong> target image here<br/>
					or <strong>PASTE</strong> by CTRL+V
				</div>
				<img v-if="targetUrl" :src="targetUrl" />
				<span v-if="targetUrl" class="arrow">&#x25c4;</span>
				<img v-if="focusResult" :src="focusResult.img" />
			</div>
			<div class="yielding">
				<a v-for="item of shownProjectedSequence" :key="item.index" class="item"
					:class="{focus: item.index === focusIndex}"
					@mouseenter="focusIndex = item.index"
					:href="generatorLinkFromLatents(item.latentCodes)"
					target="_blank"
				>
					<sup class="index">{{item.step}}.</sup>
					<img ref="sequenceImages" :src="item.img" />
				</a>
			</div>
			<Navigator />
		</main>
		<dialog class="animation" :open="showAnimationPanel" @click="showAnimationPanel = false">
			<main @click.stop="">
				<canvas ref="canvas" v-show="false" />
				<p>
					<section>
						Duration: <input type="number" v-model="animationDuration" min="100" :style="{width: '4em'}" />ms
					</section>
					<section>
						Frame rate: <input type="number" v-model="animationFPS" min="1" :style="{width: '3em'}" />fps
					</section>
				</p>
				<p>
					Dimensions: <input type="number" v-model="animationDimensions" min="4" :style="{width: '4em'}" />px
				</p>
				<p>
					<button @click="makeAnimation" :disabled="renderingAnimation">
						{{renderingAnimation ? (animationRenderProgress < projectedSequence.length ? `Copying ${animationRenderProgress} / ${projectedSequence.length}` : "Rendering...") : "Render"}}
					</button>
				</p>
				<p>
					<img v-if="animationUrl" :src="animationUrl" />
				</p>
				<p>
					<a v-if="animationUrl" :download="`${targetName}-projection-${projectedSequence.length}.gif`" :href="animationUrl">
						&#x2193;
						<span v-if="animationSize" class="size">(<em>{{animationSize.toLocaleString()}}</em> bytes)</span>
					</a>
				</p>
			</main>
		</dialog>
	</div>
</template>

<script>
	import JSZip from "jszip";
	import GIF from "gif.js.optimized";

	import StoreInput from "./storeinput.vue";
	import Navigator from "./navigator.vue";

	import * as LatentCode from "./latentCode.js";



	const MOVEMENT_THRESHOLD = 16;


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


	const downloadUrl = (url, filename) => {
		const a = document.createElement("a");
		a.setAttribute("download", filename);
		a.href = url;
		a.click();
	};



	export default {
		name: "projector",


		components: {
			StoreInput,
			Navigator,
		},


		data() {
			return {
				targetUrl: null,
				targetName: null,
				projectedSequence: [],
				projectSteps: 200,
				projectYieldInterval: 10,
				running: false,
				focusIndex: 0,
				drageHover: false,
				showAll: false,
				showAnimationPanel: false,
				animationRenderProgress: null,
				animationUrl: null,
				animationFrameInterval: 1000 / 30,
				animationDimensions: null,
				animationSize: null,
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


			shownProjectedSequence() {
				return this.showAll ? this.reversedProjectedSequence : this.reversedProjectedSequence.filter((item, i) => i === 0 || item.key);
			},


			lastKeyItem() {
				return this.reversedProjectedSequence.find(item => item.key);
			},


			focusResult() {
				const item = this.projectedSequence && this.projectedSequence[this.focusIndex];
				if (item)
					return {
						step: item.step,
						img: item.img,
						editorUrl: `/#fromW=1&psi=0.5&xlatents=${encodeURIComponent(item.latentCodes)}`,
					};

				return null;
			},


			renderingAnimation () {
				return Number.isFinite(this.animationRenderProgress);
			},


			animationDuration: {
				get () {
					return Math.round(this.projectedSequence.length * this.animationFrameInterval);
				},

				set (value) {
					if (this.projectedSequence.length)
						this.animationFrameInterval = value / this.projectedSequence.length;
				},
			},


			animationFPS: {
				get () {
					return Math.round(1000 / this.animationFrameInterval);
				},

				set (value) {
					this.animationFrameInterval = 1000 / value;
				},
			},
		},


		created() {
			window.$main = this;
			this.originTitle = document.title;
		},


		methods: {
			async onPaste(event) {
				//console.log("onPaste:", event);

				if (this.running) {
					console.warn("Projector running, please wait.");
					return;
				}

				const image = [...event.clipboardData.items].filter(item => item.type.match(/image/))[0];
				if (image)
					this.loadTargetFile(image.getAsFile());
			},


			onWheel(event) {
				//console.log("onWheel:", event);

				const oldFocusIndex = this.focusIndex;

				const direction = event.deltaY > 0 ? -1 : 1;

				this.focusIndex += direction;
				while (!this.showAll && this.projectedSequence[this.focusIndex] && !this.projectedSequence[this.focusIndex].key)
					this.focusIndex += direction;

				this.focusIndex = Math.max(Math.min(this.focusIndex, this.projectedSequence.length - 1), 0);

				if (this.focusIndex !== oldFocusIndex)
					event.preventDefault();
			},


			async onDropFiles(event) {
				this.drageHover = false;

				if (this.running) {
					console.warn("Projector running, please wait.");
					return;
				}

				const file = event.dataTransfer.files[0];
				if (file)
					if (/^image/.test(file.type))
						this.loadTargetFile(file);
					else if (/zip/.test(file.type))
						this.loadPackage(file);
			},


			loadTargetFile(file) {
				this.targetUrl = URL.createObjectURL(file);
				this.targetName = file.name.replace(/\.\w+$/, "");
			},


			async project() {
				const response = await fetch(this.targetUrl);
				const target = await response.blob();
				if (!target) {
					console.warn("target image is null.");
					return;
				}

				this.running = true;
				this.projectedSequence = [];
				this.animationUrl = null;

				try {
					for await (const result of projectImage(target, {steps: this.projectSteps, yieldInterval: this.projectYieldInterval})) {
						//console.log("project value:", value);
						const latents = LatentCode.decodeFixed16(result.latentCodes);

						/*const lastItem = this.projectedSequence[this.projectedSequence.length - 1];
						const deltaMovement = lastItem ? LatentCode.distanceBetween(latents, lastItem.latents) : null;
						console.log("deltaMovement:", deltaMovement);*/

						const distance = this.lastKeyItem && LatentCode.distanceBetween(latents, this.lastKeyItem.latents);

						this.projectedSequence.push({
							...result,
							latents,
							key: !this.lastKeyItem || distance > MOVEMENT_THRESHOLD,
							index: this.projectedSequence.length,
						});
						if (this.focusIndex >= this.projectedSequence.length - 2)
							this.focusIndex = this.projectedSequence.length - 1;
					}
				}
				catch(error) {
					console.error(error);
				}

				this.running = false;
			},


			generatorLinkFromLatents(latents) {
				return `/generate?fromW=1&xlatents=${encodeURIComponent(latents)}`;
			},


			async getSpec() {
				return (await fetch("/spec")).json();
			},


			copyLatentCode() {
				const item = this.projectedSequence && this.projectedSequence[this.focusIndex];
				if (item) {
					navigator.clipboard.writeText(`w+:${item.latentCodes}`);
					console.log("Latent code copied into clipboard.");
				}
			},


			async save () {
				const pack = new JSZip();

				const TARGET_FILE_NAME = "target.png";

				const spec = await this.getSpec();

				const target = await (await fetch(this.targetUrl)).blob();
				pack.file(TARGET_FILE_NAME, target);

				const focusItem = this.projectedSequence && this.projectedSequence[this.focusIndex];

				const resultImage = await (await fetch(focusItem.img)).blob();
				pack.file(`result-${focusItem.step}.png`, resultImage);

				const manifest = {
					usage: "stylegan-web-projector",
					model: spec.model,
					targetName: this.targetName,
					targetFile: TARGET_FILE_NAME,
					results: this.shownProjectedSequence.map(item => ({
						step: item.step,
						xlatentCode: item.latentCodes,
						key: item.key,
					})).sort((i1, i2) => i1.step - i2.step),
				};
				const manifestBlob = new Blob([JSON.stringify(manifest)], {type: "application/json"});
				pack.file("manifest.json", manifestBlob);

				const packBlob = await pack.generateAsync({type: "blob"});
				downloadUrl(URL.createObjectURL(packBlob), `${this.targetName}.projector.zip`);
			},


			async loadPackage(file) {
				const pack = await JSZip.loadAsync(file);
				const manifest = JSON.parse(await pack.file("manifest.json").async("text"));
				if (manifest.usage !== "stylegan-web-projector") {
					console.warn("unsupported package type:", manifest.usage);
					return;
				}

				console.log(`Loading package "${file.name}" with model`, manifest.model);

				const target = await pack.file(manifest.targetFile || "target.png").async("blob");
				if (!target)
					throw new Error("bad projector package, no target file.");

				this.targetUrl = URL.createObjectURL(target);
				this.targetName = manifest.targetName;

				const spec = await this.getSpec();

				if (manifest.results) {
					this.projectedSequence = manifest.results.map((result, index) => {
						let latentCodes = result.xlatentCode;
						if (!latentCodes && result.latentCode) {
							const vector = Array.from(LatentCode.decodeFloat32(result.latentCode));
							const vs = [].concat(...Array(spec.synthesis_input_shape[1]).fill(vector));
							latentCodes = LatentCode.encodeFixed16(vs);
						}

						return {
							index,
							step: result.step,
							latentCodes,
							img: this.generatorLinkFromLatents(latentCodes),
							key: result.key,
						};
					});

					this.focusIndex = this.projectedSequence.length - 1;
				}

				console.log("Done.");
			},


			async makeAnimation() {
				const spec = await this.getSpec();

				this.$refs.canvas.width = this.animationDimensions;
				this.$refs.canvas.height = Math.round(this.animationDimensions * spec.image_shape[3] / spec.image_shape[2]);
				const ctx = this.$refs.canvas.getContext("2d");
				const img = new Image();

				const gif = new GIF({
					workers: 2,
					workerScript: "/gif.worker.js",
					width: this.$refs.canvas.width,
					height: this.$refs.canvas.height,
				});

				this.animationRenderProgress = 0;
				this.animationSize = null;
				this.animationUrl = null;

				for (const item of this.projectedSequence) {
					await new Promise(resoved => {
						img.onload = resoved;
						img.src = item.img;
					});
					ctx.drawImage(img, 0, 0, this.$refs.canvas.width, this.$refs.canvas.height);

					gif.addFrame(ctx, {copy: true, delay: this.animationRenderProgress < this.projectedSequence.length - 1 ? this.animationFrameInterval : 1000});

					++this.animationRenderProgress;
				}

				const image = await new Promise(resolve => {
					gif.on("finished", resolve);
					gif.render();
				});

				this.animationRenderProgress = null;
				this.animationSize = image.size;
				this.animationUrl = URL.createObjectURL(image);
			},
		},


		watch: {
			focusIndex() {
				const focusItem = document.querySelector(".item.focus");
				if (focusItem) {
					//focusItem.scrollIntoView();
					const rect = focusItem.getBoundingClientRect();
					const visible = (rect.top >= 0) && (rect.bottom <= window.innerHeight);
					if (!visible)
						focusItem.scrollIntoView();
				}
			},


			targetName(value) {
				document.title = value ? `${this.originTitle} - ${value}` : this.originTitle;
			},


			async showAnimationPanel (value) {
				if (value) {
					const spec = await this.getSpec();
					this.animationDimensions = Math.min(spec.image_shape[2], 256);
				}
			},


			animationDimensions () {
				this.animationSize = null;
			},


			targetUrl () {
				this.animationUrl = null;
			},
		},
	};
</script>

<style>
	html
	{
		overflow: hidden;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
	}

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

	button.icon
	{
		background: transparent;
		border: 0;
		outline: 0;
		display: inline-block;
		margin: 0 1em;
		cursor: pointer;
	}

	button.icon:hover
	{
		transform: scale(1.2);
	}

	.target
	{
		text-align: center;
		padding: 20px;
	}

	.target .placeholder
	{
		padding: 2em;
		color: #ccc;
		font-size: 40px;
		width: 40vw;
		user-select: none;
	}

	.target.hover .placeholder
	{
		outline: .2em dashed #ccc;
	}

	.target > *
	{
		vertical-align: middle;
	}

	.target img
	{
		width: min(60vh, 30vw);
	}

	.target img:first-of-type
	{
		height: min(60vh, 30vw);
	}

	.target .arrow
	{
		font-size: 36px;
		display: inline-block;
		margin: 0 2em;
	}

	.yielding
	{
		max-height: calc(100vh - 4em - min(60vh, 30vw));
		width: calc(100% - 24px);
		padding: 12px;
		overflow-y: auto;
		/*white-space: nowrap;*/
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
		content: "\25c4";
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

	dialog
	{
		position: fixed;
		top: 0;
		height: 100%;
		left: 0;
		width: 100%;
		background-color: #ccca;
		cursor: pointer;
		margin: 0;
		padding: 0;
		border: 0;
	}

	dialog main
	{
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background-color: #fff;
		border-radius: 2em;
		padding: 2em;
		cursor: default;
		text-align: center;
	}

	p section
	{
		display: inline-block;
		margin: 0 1em;
	}

	.animation .size
	{
		font-size: 80%;
	}
</style>
