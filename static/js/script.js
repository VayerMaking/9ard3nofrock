const current = {
    src:undefined,
    alt:undefined,
}

function expandImgFunc(imgs) {
    var expandImg = document.getElementById("expandedImg");
    expandImg.src = imgs.src;
    current.src = imgs.src;
    current.alt = imgs.alt;
    expandImg.parentElement.style.display = "block";
}

window.onload = () => {
    first_img = new Image();
    first_img.src = 'static/images/Product.jpg';
    first_img.alt = '1';
    expandImgFunc(first_img);
}
