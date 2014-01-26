var mbiibrowser = mbiibrowser || {};

(function(ns) {
    var EP = "MBII";
    Seadragon.Config.imageLoaderLimit = 6;

    Seadragon.Config.autoHideControls = false;
    Seadragon.Config.imagePath = "lib/seadragon/img/";
    Seadragon.Config.zoomPerclick = 1.0;
    Seadragon.Viewer.prototype.hide = function() {
        var element = $(this.elmt);
        element.parent().css('display', 'none');
    };
    Seadragon.Viewer.prototype.show = function() {
        var element = $(this.elmt);
        element.parent().css('display', 'block');
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
        console.log("clicked on tag " + index);
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

    ns.MultiLayerGigapan = function(rootElement) {
        this.layers = [];
        this.viewers = [];
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
        this.bounds = new Seadragon.Rect(bounds.x, bounds.y, bounds.width, bounds.height)
        var current = this.viewers[this.currentLayer];
        if (current.viewport) {
            current.viewport.fitBounds(this.bounds, false);
        }
        this.saveBounds();
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
        console.log("viewerOpened " + viewer.layer.index);
        addTags(this.tags[0], viewer.drawer);
        if(viewer.layer.index != this.currentLayer) {
            viewer.hide();
        } else {
            this.applyBounds();
        }
        this.openedViewers = this.openedViewers + 1;
        if(this.openedViewers == this.layers.length) {
            console.log('emitting callback ' + this.openedViewers == this.layers.length);
            this.openedCallback(this);
        } else {
        }
    }

    ns.MultiLayerGigapan.prototype.createViewer = function(i) {
        var viewer;
        var layer = this.layers[i];
        viewer = new Seadragon.Viewer(layer.element[0]);
        viewer.layer = layer;
        this.viewers.push(viewer);
        console.log("createViewer " + i);
        viewer.addEventListener("open", viewerOpened.bind(this));
        viewer.addEventListener("animiationfinish", 
            (function(viewer) {
            console.log("animation finish");
            this.bounds = viewer.getBounds();}
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
        console.log("layer: " + layer.element.css('display'));
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

    ns.AjaxLoadObject = function(type, objtype, snapid, id, callback) {
        /* objtype shall be subhalo or group 
 *         type shall be json or html*/
        var source = sprintf("%s/%03d/%s/%d", type, snapid, objtype, id);
        /* hack XXX*/
        if (type == "html") type = "text";
        console.log("type");
        console.log(type);
        $.ajax({
                dataType: type,
                url: source, 
                mimeType: "application/" + type,
                type: "get"})
        .done(
             function(data) { callback(data); }
         )
        .error(
                 function(a, b, c) {
                     console.log('Ajax Failed');
                     console.log(a);
                     console.log(b);
                     console.log(c);
                 }
         );
    };

    ns.AjaxLoadTags = function(snapid, bounds, Nmax, MassMin, callback) {
        var source = sprintf("search/%03d/subhalo", snapid);
        if (! bounds) {
            bounds = {
                x: 0,
                y: 0,
                height: 10,
                width: 10 
            };
        }
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
             function(data) { callback(data); }
         )
	.error(
             function(a, b, c) {
                 console.log('Ajax Failed');
                 console.log(a);
                 console.log(b);
                 console.log(c);
             }
         );
    };

})(mbiibrowser);
