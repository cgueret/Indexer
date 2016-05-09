$(document).ready(function() {

	$('table.explorer>tbody').each(function() {
		if($(this).hasClass('collapse'))
		{
			$(this).addClass('collapsed');
		}
		else
		{
			$(this).addClass('expanded');
		}
		$(this).removeClass('collapse');
	});
	
	var c = $('section#console');
	if(c.length)
	{
		c.addClass('collapsed');	
		c.appendTo('div#console-holder');
		$('section#console>.inner>h1').on('click',function() {
			if(c.hasClass('expanded'))
			{
				c.addClass('collapsed');
				c.removeClass('expanded');
			}
			else
			{
				c.addClass('expanded');
				c.removeClass('collapsed');
			}
		});
	}
									  
	$('table.explorer tr.title').on('click',function() {
		var p = $(this).parent();
		if(p.hasClass('expanded'))
		{
			p.addClass('collapsed');
			p.removeClass('expanded');
		}
		else
		{
			p.addClass('expanded');
			p.removeClass('collapsed');
		}
	});

	var container = $('section#representations');
	if(container.length)
	{
		container.append('<h1>Representations</h1>');
		$('link[rel="alternate"]').each(function() {
			var me = $(this), title = me.attr('title'), href = me.attr('href');
			if(me === undefined || href === undefined)
			{
				return;
			}
			var el = document.createElement('section');
			var h = document.createElement('h1');
			var pre = document.createElement('pre');
			var code = document.createElement('code');
			container.append(el);
			$(el).append(h);
			$(el).data('href', href);
			$(el).addClass('collapsed');
			$(h).text(title);
			$(el).append(pre);
			$(pre).addClass('code');
			$(pre).append(code);			
			$(h).on('click', function() {
				var url = $(el).data('href');
				if(url === undefined || url === null)
				{
					if($(el).hasClass('expanded'))
					{
						$(el).addClass('collapsed');
						$(el).removeClass('expanded');
					}
					else
					{
						$(el).addClass('expanded');
						$(el).removeClass('collapsed');
					}
				}
				else
				{
					$(el).addClass('loading');
					jQuery.get(href, null, function(data) {
						if(typeof data == 'object')
						{
							console.log(data);
						}
							
						$(code).text(data);
						$(el).data('href', null);
						$(el).addClass('expanded');
						$(el).removeClass('collapsed');
						$(el).removeClass('loading');
					}, 'text');
				}
			});
		});
	}

	$('div.map').each(function() {
		var me = $(this);
		var lon = parseFloat(me.attr('data-long')), lat = parseFloat(me.attr('data-lat'));
		var zoom = 11, width = 960, height = 540, tile_size = 256;
		var xtile, ytile, north, east, south, west, tile_start, tile_end;

		function getLonLat(x, y, z)
		{			
			var n=Math.PI-2*Math.PI*y/Math.pow(2,z);
			var lon, lat;
			lon = (x/Math.pow(2,z)*360-180);
			lat = (180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n))));
			return [lon, lat];
		}

		xtile = Math.floor((lon + 180) / 360 * Math.pow(2, zoom));
		ytile = Math.floor((1-Math.log(Math.tan(lat*Math.PI/180) + 1/Math.cos(lat*Math.PI/180))/Math.PI)/2 *Math.pow(2,zoom));
		west = (xtile * tile_size - width / 2) / tile_size;		
		north = (ytile * tile_size - height / 2) / tile_size;
		east = (xtile * tile_size + width / 2) / tile_size;
		south = (ytile * tile_size + height / 2) / tile_size;
		tile_start = getLonLat(west, north, zoom);
		tile_end = getLonLat(east, south, zoom);
		me.append('<iframe src="http://www.openstreetmap.org/export/embed.html?bbox=' + tile_start[0] + ',' + tile_start[1] + ',' + tile_end[0] + ',' + tile_end[1] + '&amp;marker=' + lat + ',' + lon + '" width="' + width + '" height="' + height + '"></iframe>');		
	});
		

});
