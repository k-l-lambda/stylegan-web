
const downloadUrl = (url, filename) => {
	const a = document.createElement("a");
	a.setAttribute("download", filename);
	a.href = url;
	a.click();
};



export {
	downloadUrl,
};
