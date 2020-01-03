

function randn_bm() {
	const u = 1 - Math.random();
	const v = 1 - Math.random();
	return Math.sqrt( -2 * Math.log( u ) ) * Math.cos( 2 * Math.PI * v );
}


function encodeFloat32 (vector) {
	return btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(vector).buffer)));
}


function decodeFloat32 (code) {
	const str = atob(decodeURIComponent(code));
	const uint8 = str.split("").map(c => c.charCodeAt(0));
	return new Float32Array(new Uint8Array(uint8).buffer);
}


function encodeFixed16 (vector) {
	return btoa(String.fromCharCode.apply(null, new Uint8Array(new Int16Array(vector.map(x => Math.floor(Math.min(Math.max(x, -32), 32 - 1e-9) * 1024))).buffer)));
}


function decodeFixed16 (code) {
	const str = atob(decodeURIComponent(code));
	const uint8 = str.split("").map(c => c.charCodeAt(0));
	const int16 = new Int16Array(new Uint8Array(uint8).buffer);
	return Array.from(int16).map(x => x / 1024);
}


function normalize(v) {
	const magnitude = Math.sqrt(v.reduce((s, x) => s + x * x, 0));

	return v.map(x => x / magnitude);
}


function angleBetween(v1, v2) {
	const nv1 = normalize(v1);
	const nv2 = normalize(v2);

	const dotProduct = nv1.reduce((sum, x, i) => sum + x * nv2[i], 0);

	return Math.acos(Math.max(Math.min(dotProduct, 1), -1));
}


function distanceBetween(v1, v2) {
	return Math.sqrt(v1.reduce((sum, x, i) => sum + (x - v2[i]) ** 2, 0));
}



export {
	randn_bm,
	decodeFloat32,
	encodeFloat32,
	encodeFixed16,
	decodeFixed16,
	normalize,
	angleBetween,
	distanceBetween,
};
