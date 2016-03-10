
function createGauge(name, label, min, max, size, gauges)
{
  var config =
  {
    size: undefined != size ? size : 240,
    label: label,
    min: undefined != min ? min : 0,
    max: undefined != max ? max : 100,
    minorTicks: 5
  }

  var range = config.max - config.min;
  config.redZones = [{ from: config.min + range*0, to: config.min + range*0.25 }];
  //config.yellowZones = [{ from: config.min + range*0.25, to: config.min + range*0.50 }];
  config.greenZones = [{ from: config.min + range*0.70, to: config.max }];

  gauges[name] = new Gauge(name, config);
  gauges[name].render();
}

function createGauges(gauges)
{
  createGauge("F1", "THPUT-1", 0 , 1000, 125, gauges);
  createGauge("F2", "THPUT-2", 0 , 1000, 125, gauges);
  createGauge("F3", "THPUT-3", 0 , 1000, 125, gauges);
  createGauge("F4", "THPUT-4", 0 , 1000, 125, gauges);

  createGauge("B1", "THPUT-1", 0 , 1000, 125, gauges);
  createGauge("B2", "THPUT-2", 0 , 1000, 125, gauges);
  createGauge("B3", "THPUT-3", 0 , 1000, 125, gauges);
  createGauge("B4", "THPUT-4", 0 , 1000, 125, gauges);
}

function updateGauges()
{
  for (var key in gauges)
  {
    var value = getRandomValue(gauges[key])
    gauges[key].redraw(value);
  }
}
