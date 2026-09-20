(function() {
    const myGame = window.myGame;

    const canvas = myGame.canvas;
    canvas.style.display = 'block';
    canvas.focus();
    function getClosestMultiplier(baseWidth, baseHeight, windowWidth, windowHeight) {
        const maxWidthMultiplier = Math.floor(windowWidth / baseWidth);
        const maxHeightMultiplier = Math.floor(windowHeight / baseHeight);
        const maxMultiplier = Math.min(maxWidthMultiplier, maxHeightMultiplier);

        let multiplier = maxMultiplier;

        // Try to adjust for .25, .50, .75 steps
        while (multiplier > 0) {
            let candidateMultipliers = [multiplier, multiplier + 0.25, multiplier + 0.5, multiplier + 0.75].filter(
                m => baseWidth * m <= windowWidth && baseHeight * m <= windowHeight
            );

            if (candidateMultipliers.length > 0) {
                return candidateMultipliers[candidateMultipliers.length - 1];
            }
            multiplier -= 1;
        }
        return 1;
    }
    function resizeCanvas() {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;

        let selectedMultiplier = getClosestMultiplier(myGame.baseWidth, myGame.baseHeight, windowWidth, windowHeight);

        const newWidth = myGame.baseWidth * selectedMultiplier;
        const newHeight = myGame.baseHeight * selectedMultiplier;

        canvas.style.width = `${newWidth}px`;
        canvas.style.height = `${newHeight}px`;  // decimal multipliers are not good for pixel art. most devices should be max resolution anyway
        console.log(`canvas size: ${newWidth}px x ${newHeight}px Multiplayer: ${selectedMultiplier}`)
    }


    function isMobileDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
	}

    // Loading is a single multi-megabyte fetch + a synchronous unzip, which can
    // take a long time on a slow mobile connection. Without visible progress a
    // slow load and a stuck one look identical, so track progress and surface a
    // stall warning instead of leaving a static "Loading..." on screen forever.
    let lastProgressAt = Date.now();
    function setLoadingText(text) {
        lastProgressAt = Date.now();
        if (myGame.LoadingOverlay) {
            myGame.LoadingOverlay.innerText = text;
        }
    }
    setInterval(() => {
        const stalledFor = Date.now() - lastProgressAt;
        if (stalledFor > 20000 && myGame.LoadingOverlay && myGame.LoadingOverlay.style.display !== 'none') {
            const seconds = Math.floor(stalledFor / 1000);
            const base = myGame.LoadingOverlay.innerText.split('\n')[0];
            myGame.LoadingOverlay.innerText = `${base}\nStill working (${seconds}s) — large file, please wait on slow connections.`;
        }
    }, 5000);

    async function fetchWithProgress(url, label) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load ${url}: ${response.status} ${response.statusText}`);
        }
        const total = Number(response.headers.get('content-length')) || 0;
        if (!response.body || !response.body.getReader) {
            setLoadingText(`${label}…`);
            return new Uint8Array(await response.arrayBuffer());
        }
        const reader = response.body.getReader();
        const chunks = [];
        let received = 0;
        let lastShown = -1;
        for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
            received += value.length;
            if (total) {
                const pct = Math.min(100, Math.floor((received / total) * 100));
                if (pct !== lastShown) {
                    lastShown = pct;
                    setLoadingText(`${label}… ${pct}%`);
                }
            } else {
                const mb = Math.floor(received / 1048576);
                if (mb !== lastShown) {
                    lastShown = mb;
                    setLoadingText(`${label}… ${mb}MB`);
                }
            }
        }
        const result = new Uint8Array(received);
        let offset = 0;
        for (const chunk of chunks) {
            result.set(chunk, offset);
            offset += chunk.length;
        }
        return result;
    }

    myGame.unzipFile = async function(zipFilePath) {
        try {
            const bytes = await fetchWithProgress(zipFilePath, 'Downloading engine');
            setLoadingText('Unpacking engine…');
            let unzipData;
            try {
                unzipData = fflate.unzipSync(bytes);
            } catch (error) {
                console.error(`Error during unzipping ${zipFilePath}:`, error);
                throw error;
            }

            if (unzipData) {
                const result = {};
                const mimeTypeMap = {
                    'txt': 'text/plain',
                    'html': 'text/html',
                    'js': 'application/javascript',
                    'css': 'text/css',
                    'json': 'application/json',
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'svg': 'image/svg+xml',
                    'mp3': 'audio/mpeg',
                    'wav': 'audio/wav',
                    'mp4': 'video/mp4',
                    'webm': 'video/webm',
                    'wasm': 'application/wasm',
                    'webp': 'image/webp'
                    // Add more mappings as needed
                };

                for (const filename in unzipData) {
                    const fileData = unzipData[filename];
                    const extension = filename.split('.').pop().toLowerCase();
                    const mimeType = mimeTypeMap[extension] || 'application/octet-stream';

                    const blob = new Blob([fileData], { type: mimeType });
                    const blobURL = URL.createObjectURL(blob);
                    result[filename] = blobURL;
                }

                return result;
            } else {
                throw new Error(`Unzipping ${zipFilePath} failed, unzipData is undefined`);
            }
        } catch (error) {
            console.error(`Failed to unzip file ${zipFilePath}:`, error);
            throw error;
        }
    };

    myGame.unzipToFS = async function(zipFilePaths) {
        const zipFiles = Array.isArray(zipFilePaths) ? zipFilePaths : [zipFilePaths];
        try {
            for (const zipFilePath of zipFiles) {

                const bytes = await fetchWithProgress(zipFilePath, 'Downloading game data');
                setLoadingText('Unpacking game data…');

                let unzipData;
                try {
                    unzipData = fflate.unzipSync(bytes);
                } catch (error) {
                    console.error(`Error during unzipping ${zipFilePath}:`, error);
                    throw error;
                }

                if (unzipData) {
                    const foldersToCreate = new Set();
                    const filesToWrite = new Set();

                    for (let filename in unzipData) {
                        const fileData = unzipData[filename];
                        const fullPath = '/' + filename;
                        const folderPath = fullPath.substring(0, fullPath.lastIndexOf('/'));

                        if (fileData.length === 0) {
                            foldersToCreate.add(folderPath);
                        } else {
                            filesToWrite.add({ fullPath, fileData });
                        }
                    }

                    foldersToCreate.forEach(folderPath => {
                        try {
                            FS.mkdirTree(folderPath);
                        } catch (e) {
                            console.warn(`Folder creation skipped or failed for ${folderPath}:`, e);
                        }
                    });

                    setLoadingText('Installing files…');
                    let written = 0;
                    const totalFiles = filesToWrite.size;
                    filesToWrite.forEach(({ fullPath, fileData }) => {
                        try {
                            FS.writeFile(fullPath, fileData);
                        } catch (error) {
                            console.error(`Error writing file ${fullPath}:`, error);
                        }
                        written++;
                        if (written % 100 === 0) {
                            setLoadingText(`Installing files… ${written}/${totalFiles}`);
                        }
                    });
                    setLoadingText('Starting engine…');
                } else {
                    throw new Error(`Unzipping ${zipFilePath} failed, unzipData is undefined`);
                }
            }
        } catch (error) {
            console.error('Failed to unzip to FS:', error);
            throw error;
        }
    };

    function unzipOpenBOR() {
        return myGame.unzipFile(myGame.paths['OpenBOR.zip'], {
        }).then(result => {
            myGame.unzippedFiles = result;
        });
    }

    function startGame() {
		window.Module= {
			locateFile: function(path) {
				if (path.endsWith('.wasm')) {
					return myGame.unzippedFiles['OpenBOR.wasm'];
				}
				return path;
			},
			preRun: [
				function() {
					window.Module.addRunDependency('unpack');

                    try {
                        FS.mkdir('/Paks');
                    } catch (e) {
                        console.log("/Paks directory already exists");
                    }
                    const pakFilename = `${document.title}.pak`;
					if (myGame.assetType === 'pak') {
						FS.createPreloadedFile('/Paks', pakFilename, myGame.paths.assetsPaths[0], true, false,
							function() {
								console.log(`Successfully loaded ${pakFilename}`);
								window.Module.removeRunDependency('unpack');
                                myGame.LoadingOverlay.style.display = 'none';
							},
							function() {
								console.error(`Successfully loaded ${pakFilename}`);
								window.Module.removeRunDependency('unpack');
                                myGame.LoadingOverlay.innerText = 'Unpacking error';
							}
						);
						window.Module.arguments = [];
					} else {
						myGame.unzipToFS(myGame.paths.assetsPaths)
							.then(() => {
                                try {
                                    FS.writeFile(`/Paks/${pakFilename}`, new Uint8Array());
                                    console.log(`Created empty pak file: /Paks/${pakFilename}`);
                                } catch (e) {
                                    console.error(`Failed to create empty pak file: /Paks/${pakFilename}`, e);
                                }
								window.Module.removeRunDependency('unpack');
                                myGame.LoadingOverlay.style.display = 'none';
							})
							.catch(error => {
								console.error('Failed to unzip game files:', error);
								window.Module.removeRunDependency('unpack');
                                myGame.LoadingOverlay.innerText = 'Unpacking error';
							});
					};
				}
			],
			arguments: [],
			canvas: myGame.canvas,
			onRuntimeInitialized: function() {
				console.log('WASM module initialized');
			},
			print: function(text) {
				console.log(text);
			},
			printErr: function(text) {
				console.error(text);
			},
			setStatus: function(text) {
				if (text) {
					console.log(text);
				}
			}
		};

        const script = document.createElement('script');
        script.id = 'openbor-script';
        script.src = myGame.unzippedFiles['OpenBOR.js'];
        script.onload = () => {
            console.log('OpenBOR.js script loaded');
        };
        script.onerror = () => {
            console.error('Failed to load OpenBOR.js script');
        };
        document.body.appendChild(script);
    }

    function initGame() {

        if (isMobileDevice()) {
            const  mobileScript = document.createElement('script');
            mobileScript.src = myGame.paths['mobile.js'];
            mobileScript.onload = function() {
                console.log('Mobile script loaded');
            };
            mobileScript.onerror = function() {
                console.error('Failed to load mobile.js');
            };
            document.head.appendChild(mobileScript);
        }

        unzipOpenBOR().then(() => {
            startGame();
        }).catch((error) => {
            console.error('Failed to unzip and prepare OpenBOR:', error);
        });
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const fflateScript = document.createElement('script');
    fflateScript.src = myGame.paths['fflate.min.js'];
    fflateScript.onload = () => {
        initGame();
    };
    fflateScript.onerror = () => {
        console.error('Failed to load fflate script');
    };
    document.head.appendChild(fflateScript);

})();