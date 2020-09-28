function circle(x, y, radius, lw, ctx) {
  ctx.beginPath();
  ctx.lineWidth = lw;
  ctx.arc(x, y, radius, 0, 2 * Math.PI);
  ctx.closePath();
  ctx.stroke();
}

function elaztoxy(el, az, x, y, ctx) {

  var a = Math.sin(az*2*Math.PI/360);
  var b = -Math.cos(az*2*Math.PI/360);
  el = (90-el)/90*200;
  return [a*el+x, b*el+y];
}

function drawMap(ctx) {
  circle(220, 220, 200, 2, ctx);
  circle(220, 220, 133, 0.5, ctx);
  circle(220, 220, 66, 0.5, ctx);

  ctx.beginPath();
  ctx.moveTo(220,20);
  ctx.lineTo(220,420);
  ctx.moveTo(20,220);
  ctx.lineTo(420,220);
  ctx.stroke();
}

function drawLabels(ctx){
  ctx.font = "15px Arial";
  ctx.fillStyle = "black";
  ctx.fillText("N", 215, 15);
  ctx.fillText("E", 425, 225);
  ctx.fillText("S", 216, 435);
  ctx.fillText("W", 2, 225);

}

function define_circle(p1, p2, p3){
    temp = p2[0] * p2[0] + p2[1] * p2[1];
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2;
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2;
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1]);

    cx = (bc*(p2[1] - p3[1]) - cd*(p1[1] - p2[1])) / det;
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det;

    radius = Math.sqrt((cx - p1[0])**2 + (cy - p1[1])**2);
    ret= [cx,cy,radius]
    return ret;
}

function circleb(x, y, radius, lw, ctx, a, b, c) {
ctx.strokeStyle = "#FF7700";
  ctx.beginPath();
  ctx.lineWidth = lw;

  ctx.arc(x, y, radius, 0, 2*Math.PI);
  ctx.stroke();
}

function drawPass(ctx, par){
  if(par[3]==0) par[3] = 1;
    c = define_circle(elaztoxy(0, par[0], 220, 220),
                elaztoxy(par[3], par[1], 220, 220),
                elaztoxy(0, par[2], 220, 220) );
  p1 = elaztoxy(0, par[0], 220, 220);
  p2 = elaztoxy(0, par[2], 220, 220);
  p3 = elaztoxy(par[3], par[1], 220, 220);

  a1 = Math.atan2(c[1] - p1[1], c[0] - p1[0]);
  a2 = Math.atan2(c[1] - p2[1], c[0] - p2[0]);
  a3 = Math.atan2(c[1] - p3[1], c[0] - p3[0]);

  circleb(c[0], c[1], c[2], 2, ctx, a1, a2, a3);
  ctx.strokeStyle = "#00FF00";
  circle(p1[0], p1[1], 6, 4, ctx);
  ctx.strokeStyle = "#FF0000";
  circle(p2[0], p2[1], 6, 4, ctx);

        ctx.font = "30px Arial";

        ctx.fillStyle = "#00CC00";
        ctx.fillText("↑", 15, 25);
        ctx.fillStyle = "#FF0000";
        ctx.fillText("↓", 30, 25);
}

function draw(ctx, params) {
	drawMap(ctx);
	drawPass(ctx, params.split(','));

	var maskCanvas = document.createElement('canvas');
	maskCanvas.width = canvas.width;
	maskCanvas.height = canvas.height;
	var maskCtx = maskCanvas.getContext('2d');

	maskCtx.fillStyle = "white";
	maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);
	maskCtx.globalCompositeOperation = 'xor';
	maskCtx.arc(220, 220, 200, 0, 2 * Math.PI);
	maskCtx.fill();

	ctx.drawImage(maskCanvas, 0, 0);

	drawLabels(ctx);
}
