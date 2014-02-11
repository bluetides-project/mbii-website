var mbiibrowser = mbiibrowser || {};

(function(ns) {
    var EP = "MBII";
    Seadragon.Config.imageLoaderLimit = 6;

    Seadragon.Config.autoHideControls = false;
    Seadragon.Config.imagePath = "lib/seadragon/img/";
    Seadragon.Config.zoomPerClick = 1.0;
    Seadragon.Viewer.prototype.hide = function() {
        var element = $(this.elmt);
        element.parent().css('display', 'none');
    };
    Seadragon.Viewer.prototype.show = function() {
        var element = $(this.elmt);
        element.parent().css('display', 'block');
    };

    ns.ProgressMonitor = function(working, done, failed) {
        this.elmt = {
            working: $(working),
            done: $(done),
            failed: $(failed),
        };
        this.elmt.working.hide();
        this.elmt.done.hide();
        this.elmt.failed.hide();
        this.value = 0;
    };

    ns.ProgressMonitor.prototype.start = function() {
        this.value = this.value + 1;
        if(this.value > 0) {
            this.elmt.done.hide();
            this.elmt.failed.hide();
            this.elmt.working.show();
        }
    };

    ns.ProgressMonitor.prototype.done = function() {
        this.value = this.value - 1;
        if(this.value <= 0) {
            this.elmt.done.show();
            this.elmt.failed.hide();
            this.elmt.working.hide();
        }
    };

    ns.ProgressMonitor.prototype.failed = function(reason) {
        this.value = this.value - 1;
        this.elmt.done.hide();
        this.elmt.working.hide();
        if(reason) {
            this.elmt.failed.text(reason);
        }
        this.elmt.failed.show();
    };


    ns.MultiLayerTags = function(klass, callback) {
        /* when tag is clicked, call callback(this, i) */
        this.desc = [];
        this.length = 0;
        this.klass = klass;
        this.callback = callback;
    };

    ns.MultiLayerTags.prototype.setDesc = function(desc) {
        this.desc = desc;
        this.length = desc.length;
    };

    function tagClicked(event) {
        var index = event.data;
        this.callback(this, index);
        event.preventDefault();
    }

    ns.MultiLayerTags.prototype.getElement = function(i) {
        var tag = this.desc[i];
        if (tag.element) return tag.element;
        var element = $('<div>', {class: this.klass, index: i});
        if (tag.content.iscentral) element.addClass("Central");
        tag.element = element;
        element.click(i, tagClicked.bind(this));
        return element;
    };

    ns.MultiLayerTags.prototype.getCenter = function(i) {
        var tag = this.desc[i];
        return new Seadragon.Point(1.0 * tag.center.x, 1.0 * tag.center.y);
    }

    ns.MultiLayerTags.prototype.getAttr = function(name, i) {
        var tag = this.desc[i];
        return tag[name];
    }

    ns.Scale = function(rootElement, units, factor) {
        /* units is {str:, factor} */
        this.rootElement = rootElement;
        this.element = $('<div></div>');
        this.labelElement = $('<span>Scale</span>');
        this.element.append(this.labelElement);
        var bar = $('<hr/>');
        bar.css('height',  '2px');
        bar.css('color',  'white');
        bar.css('border',  'none');
        bar.css('background-color',  'white');
        this.element.append(bar);
        this.element.css('position', "absolute");
        this.element.css('width', "200px");
        this.element.css('text-align', "center");
        this.element.css('color', "white");
        this.element.css('bottom', "20px");
        this.element.css('z-index', "199999999");
        this.rootElement.append(this.element);
        this.units = units;
        this.factor = factor;
        this.width = 200;
    };

    ns.Scale.prototype.setLabel = function (label) {
        this.labelElement.text(label);
    };

    ns.Scale.prototype.redraw = function () {
        this.element.css('width', sprintf('%dpx', this.width));
        this.element.css("left", (this.rootElement.width() - this.width) / 2);
    }
    ns.Scale.prototype.fit = function (viewer) {
        var width = this.calculateScaleWidth(viewer);
        this.setLabel(width.label);
        this.setWidth(width.pixels);
    };

    ns.Scale.prototype.setWidth = function (width) {
        this.width = width;
        this.redraw();
    };

    ns.Scale.prototype.calculateScaleWidth = function (viewer) {
        var pt;
        var pointlen = 2.0;
        var pxlen = 0;
        while(pxlen < 100 || pxlen > 200) {
            pointlen = pointlen * 0.5;
            pt = new Seadragon.Point(pointlen, 0.0);
            pxlen = viewer.viewport.deltaPixelsFromPoints(pt, true).x;
        }
        var i;
        var tmp;
        var physlen;
        for(i = 0; i < this.units.length; i ++) {
            tmp = pointlen * this.factor / this.units[i].factor;
            if (tmp < 1) break; 
        }
        i = (i >0)?i-1:0;
        physlen = pointlen * this.factor / this.units[i].factor;
        physlen = parseFloat(Number(physlen).toPrecision(1));
        pointlen = physlen * this.units[i].factor / this.factor;
        pxlen = viewer.viewport.deltaPixelsFromPoints(
                new Seadragon.Point(pointlen, 0.0), true).x;
        label = sprintf("%f %s", physlen, this.units[i].str);
        return {pixels: pxlen, points: pointlen, label: label};
    }

    ns.MultiLayerGigapan = function(rootElement, scale) {
        this.layers = [];
        this.viewers = [];
        this.scale = scale;
        this.currentLayer = 0;
        this.rootElement = rootElement;
        this.bounds = null;
        this.tags = [];
    };

    ns.MultiLayerGigapan.prototype.open = function(layers, callback) {
        var i;
        var element;
        for (i = 0; i < layers.length; i++) {
            element = $('<div>', {
                id: EP + "Gigapan" + layers[i].id,
            });
            element.height(this.height);
            $(this.rootElement).append(element);
            layers[i].element = element;
            layers[i].index = i;
            this.layers.push(layers[i]);
        }
        this.openedCallback = callback;
        this.openedViewers = 0;
        for (i = 0; i < layers.length; i++) {
            this.createViewer(i);
        }
    };
    ns.MultiLayerGigapan.prototype.saveBounds = function() {
        var old;
        old = this.viewers[this.currentLayer];
        if(old && old.viewport) {
            this.bounds = old.viewport.getBounds();
        }
    };
    ns.MultiLayerGigapan.prototype.applyBounds = function() {
        var current = this.viewers[this.currentLayer];
        if (this.bounds !== null && current.viewport) {
            current.viewport.fitBounds(this.bounds, true);
        }
    };
    ns.MultiLayerGigapan.prototype.view = function(bounds) {
        var bounds = new Seadragon.Rect(bounds.x, bounds.y, bounds.width + bounds.x * 0.0001, bounds.height + bounds.y * 0.0001);
        var current = this.viewers[this.currentLayer];
        if (current.viewport) {
            current.viewport.fitBounds(current.viewport.getBounds(), true);
            current.viewport.fitBounds(bounds, false);
        }
        this.bounds = bounds;
    };

    ns.MultiLayerGigapan.prototype.reopen = function(layers, callback) {
        /* layers will have width, height and gigapan id*/
        var i;
        /* this will save the bounds */
        this.saveBounds();
        for (i = 0; i < this.layers.length; i++) {
            $(this.layers[i].element).remove();
        }
        this.layers = [];
        this.viewers = [];
        this.open(layers, callback);
    };

    ns.MultiLayerGigapan.prototype.resize = function(height) {
        var i;
        this.height = height;
        this.scale.redraw();
        for (i = 0; i < this.layers.length; i++) {
            this.layers[i].element.height(height);
        }
    };

    ns.MultiLayerGigapan.prototype.clearTags = function(mlt) {
        this.tags = [];
        for (i = 0; i < this.viewers.length; i ++) {
            if (this.viewers[i].drawer) {
                this.viewers[i].drawer.clearOverlays();
            }
        }
    };

    ns.MultiLayerGigapan.prototype.addTags = function(mlt) {
        this.tags.push(mlt);
    };

    ns.MultiLayerGigapan.prototype.drawTags = function(mlt) {
        var i = 0;
        var j = 0;
        var viewer;
        for(i = 0; i < this.viewers.length; i ++) {
            viewer = this.viewers[i];
            if (viewer.drawer) {
                viewer.drawer.clearOverlays();
            }
        }
        i = this.currentLayer;
        viewer = this.viewers[i];
        if (viewer.drawer) {
            /* draw tags only on the currentLayer */
            for (j = 0; j < this.tags.length; j ++) {
                addTags(this.tags[j], viewer.drawer); 
            }
        }
    };

    function addTags(tags, drawer) {
        var i;
        for (i = 0; i < tags.length; i++) {
            var element = tags.getElement(i);
            var center = tags.getCenter(i);
            drawer.addOverlay(element[0], center, Seadragon.OverlayPlacement.CENTER);
        }
    }

    function viewerOpened(viewer) {
        addTags(this.tags[0], viewer.drawer);
        if(viewer.layer.index != this.currentLayer) {
            viewer.hide();
        } else {
            this.applyBounds();
            animationHandler.apply(this, [viewer]);
        }
        this.openedViewers = this.openedViewers + 1;
        if(this.openedViewers == this.layers.length) {
            this.openedCallback(this);
        } else {
        }
    }

    function animationHandler(viewer) {
        this.scale.fit(viewer);
    }

    ns.MultiLayerGigapan.prototype.createViewer = function(i) {
        var viewer;
        var layer = this.layers[i];
        viewer = new Seadragon.Viewer(layer.element[0]);
        viewer.layer = layer;
        this.viewers.push(viewer);
        viewer.addEventListener("open", viewerOpened.bind(this));
        viewer.addEventListener("animation", animationHandler.bind(this));
        viewer.addEventListener("animationfinish", 
            (function(viewer) {
            this.bounds = viewer.viewport.getBounds();}
            ).bind(this)
        );
        openTiles(viewer, layer);
    };

    ns.MultiLayerGigapan.prototype.switchLayer = function(layerIndex) {
        var i;
        this.saveBounds();
        for(i = 0; i < this.viewers.length; i ++) {
            if (i == layerIndex) continue;
            this.viewers[i].hide();
        }
        this.currentLayer = layerIndex;
        var current = this.viewers[layerIndex];
        if (current) {
            current.show();
        }
        this.applyBounds();
        this.drawTags();
    }
    function openTiles(viewer, layer) {
        viewer.setDashboardEnabled(true);
        //
        // compute the index of the tile server for this gigapan 
        // (note: this may change in the future, perhaps without warning!)
        var tileServerIndex = '' + Math.floor(layer.id / 1000);
        if (tileServerIndex.length < 2) {
           tileServerIndex = '0' + tileServerIndex;
        }

        var urlPrefix = "http://tile" + tileServerIndex + ".gigapan.org/gigapans0/" + layer.id + "/tiles";

        // create the tile source
        var gigapanSource = new org.gigapan.seadragon.GigapanTileSource(
              urlPrefix,
              layer.width,
              layer.height
        );

        // tell the viewer to open the tile source
        viewer.openTileSource(gigapanSource);
    }

    ns.AjaxLoadObject = function(type, objtype, snapid, id, callback, monitor) {
        /* objtype shall be subhalo or group 
 *         type shall be json or html*/
        var source = sprintf("%s/%03d/%s/%d", type, snapid, objtype, id);
        /* hack XXX*/
        if (type == "html") type = "text";
        monitor.start();
        $.ajax({
                dataType: type,
                url: source, 
                mimeType: "application/" + type,
                type: "get"})
        .done(
            function(data) { callback(data); 
                monitor.done();
            }
        )
        .error(
            function(a, b, c) {
                console.log('Ajax Failed');
                console.log(a);
                console.log(b);
                console.log(c);
                monitor.failed();
            }
        );
    };

    ns.AjaxLoadTags = function(snapid, bounds, Nmax, MassMin, callback, monitor) {
        var source = sprintf("search/%03d/subhalo", snapid);
        if (! bounds) {
            bounds = {
                x: 0,
                y: 0,
                height: 10,
                width: 10 
            };
        }
        monitor.start();
        $.ajax({
                dataType: "json",
                url: source, 
                mimeType: "application/json",
                type: "post",
                data: {ymin: bounds.y, ymax: bounds.y + bounds.height,
                       xmin: bounds.x, xmax: bounds.x + bounds.width, 
                       MassMin: MassMin,
                        Nmax: Nmax}
                      })
        .done(
            function(data) { callback(data); monitor.done(); }
         )
        .error(
            function(a, b, c) {
                monitor.failed();
                console.log('Ajax Failed');
                console.log(a);
                console.log(b);
                console.log(c);
            }
        );
    };

})(mbiibrowser);
