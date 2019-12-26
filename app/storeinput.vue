<template>
	<span class="storeinput">
		<input
			:type="type"
			v-model.lazy="innerValue"
			:style="styleObj"
			:placeholder="placeholder"
			:min="range && range.min"
			:max="range && range.max"
			:step="range && range.step"
			:disabled="disabled"
		/>
	</span>
</template>

<script>
	export default {
		name: "store-input",


		props: {
			type: {
				type: String,
				default: "text",
			},

			value: {
				validator () {return true;},
			},

			range: Object,

			styleObj: Object,

			placeholder: String,

			localKey: String,
			sessionKey: String,

			disabled: Boolean,
		},


		computed: {
			innerValue: {
				get () {
					return this.value;
				},

				set (value) {
					this.$emit("input", value);
				},
			},
		},


		created () {
			this.load();
		},


		methods: {
			load () {
				if (this.localKey && localStorage[`storeInput-${this.localKey}`])
					this.innerValue = JSON.parse(localStorage[`storeInput-${this.localKey}`]);

				if (this.sessionKey && sessionStorage[`storeInput-${this.sessionKey}`])
					this.innerValue = JSON.parse(sessionStorage[`storeInput-${this.sessionKey}`]);
			},


			save () {
				if (this.localKey)
					localStorage[`storeInput-${this.localKey}`] = JSON.stringify(this.value);

				if (this.sessionKey)
					sessionStorage[`storeInput-${this.sessionKey}`] = JSON.stringify(this.value);
			},
		},


		watch: {
			value: "save",
		},
	};
</script>

<style scoped>
	.storeinput
	{
		position: relative;
	}
</style>
