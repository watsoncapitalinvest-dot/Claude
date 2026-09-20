(function() {
    const myGame = window.myGame;
    
    const nippleScript = document.createElement('script');
    nippleScript.src = myGame.paths['nipplejs.min.js'];

    nippleScript.onload = () => {
        setupTouchControls();
        unzipButtons().then(() => {
            const buttonsOverlay = myGame.buttonsOverlay;
            buttonsOverlay.style.pointerEvents = 'auto';
            createButtonsOverlay();
        }).catch((error) => {
            console.error('Failed to unzip and prepare buttons:', error);
        });
    };

    nippleScript.onerror = () => {
        console.error('Failed to load nipplejs.js');
    };

    document.head.appendChild(nippleScript);

    function unzipButtons() {
        return myGame.unzipFile(myGame.paths['buttons.zip']).then(result => {
            myGame.buttonImages = result;
        });
    }

    function setupTouchControls() {
        const canvas = myGame.canvas;
        const overlay = myGame.overlay;
        overlay.style.pointerEvents = 'auto';

        const keyCodeMap = {
            'left': 37,
            'up': 38,
            'right': 39,
            'down': 40
        };

        const directionMap = {
            'left': ['left'],
            'up-left': ['up', 'left'],
            'up': ['up'],
            'up-right': ['up', 'right'],
            'right': ['right'],
            'down-right': ['down', 'right'],
            'down': ['down'],
            'down-left': ['down', 'left']
        };

        let activeKeys = {
            'left': false,
            'up': false,
            'right': false,
            'down': false
        };

        let joystickManager = null;

        function getDirectionFromAngle(angle) {
            if (angle >= 67.5 && angle < 112.5) return 'up';
            if (angle >= 112.5 && angle < 157.5) return 'up-left';
            if (angle >= 157.5 && angle < 202.5) return 'left';
            if (angle >= 202.5 && angle < 247.5) return 'down-left';
            if (angle >= 247.5 && angle < 292.5) return 'down';
            if (angle >= 292.5 && angle < 337.5) return 'down-right';
            if ((angle >= 337.5 && angle <= 360) || (angle >= 0 && angle < 22.5)) return 'right';
            if (angle >= 22.5 && angle < 67.5) return 'up-right';
        }

        function updateKeys(keys) {
            const newActiveKeys = {
                'left': keys.includes('left'),
                'up': keys.includes('up'),
                'right': keys.includes('right'),
                'down': keys.includes('down')
            };

            Object.keys(keyCodeMap).forEach(key => {
                const keyCode = keyCodeMap[key];
                if (newActiveKeys[key] !== activeKeys[key]) {
                    activeKeys[key] = newActiveKeys[key];
                    triggerKeyboardEvent(keyCode, newActiveKeys[key] ? 'keydown' : 'keyup');
                }
            });
        }

        function releaseAllKeys() {
            Object.keys(activeKeys).forEach(key => {
                const keyCode = keyCodeMap[key];
                if (activeKeys[key]) {
                    activeKeys[key] = false;
                    triggerKeyboardEvent(keyCode, 'keyup');
                }
            });
        }

        function triggerKeyboardEvent(keyCode, eventType) {
            const event = new KeyboardEvent(eventType, {
                key: keyCode === 38 ? 'ArrowUp' : keyCode === 40 ? 'ArrowDown' : keyCode === 37 ? 'ArrowLeft' : 'ArrowRight',
                code: 'Arrow' + (keyCode === 38 ? 'Up' : keyCode === 40 ? 'Down' : keyCode === 37 ? 'Left' : 'Right'),
                keyCode: keyCode,
                bubbles: true
            });
            canvas.dispatchEvent(event);
        }

        function updateJoystick() {
            if (joystickManager) {
                joystickManager.destroy();
            }
            overlay.innerHTML = '';

            joystickManager = nipplejs.create({
                zone: overlay,
                color: 'white',
                threshold: 0.3,
                fadeTime: 0
            });

            joystickManager.on('move', function(evt, data) {
                if (data.direction) {
                    const direction = getDirectionFromAngle(data.angle.degree);
                    const keys = directionMap[direction] || [];
                    updateKeys(keys);
                } else {
                    releaseAllKeys();
                }
            });

            joystickManager.on('end', function() {
                releaseAllKeys();
            });
        }

        updateJoystick();
        myGame.releaseAllKeys = releaseAllKeys;
        myGame.updateJoystick = updateJoystick;

    }

    function createButtonsOverlay() {
        const canvas = myGame.canvas;
        const buttonsOverlay = myGame.buttonsOverlay;

        const buttonsConfig = [
            { id: 'attack-button', className: 'button', src: 'attack.png', alt: 'Attack', keyCode: 65, style: { bottom: '5%', right: '27.5%', width: '20%' } },
            { id: 'jump-button', className: 'button', src: 'jump.png', alt: 'Jump', keyCode: 68, style: { bottom: '5%', right: '5%', width: '20%' } },
            { id: 'star-button', className: 'button', src: 'star.png', alt: 'Star', keyCode: 70, style: { bottom: '17.5%', right: '16%', width: '20%' } },
            { id: 'pause-button', className: 'button', src: 'pause.png', alt: 'Pause', keyCode: 13, style: { top: '27.5%', right: '5%', width: '15%' } },
            { id: 'fullscreen-button', className: 'button', src: 'full.png', alt: 'Fullscreen', action: toggleFullscreen, style: { top: '15%', right: '5%', width: '15%' } },
            // OpenBOR's arcade menu needs "insert coin" (5) then "1P start" (1)
            // before it will let a match begin at all. Neither key had any
            // on-screen control, so a touch-only player had no way to ever
            // get past the title/menu screen — this was the actual "controls
            // don't work" bug, not a rendering issue. Plain text buttons
            // since there's no icon asset for these.
            { id: 'coin-button', className: 'button text-button', label: 'COIN', keyCode: 53, style: { top: '5%', left: '5%', width: '18%' } },
            { id: 'p1start-button', className: 'button text-button', label: '1P START', keyCode: 49, style: { top: '5%', left: '25%', width: '22%' } }
        ];

        buttonsConfig.forEach(config => {
            const button = document.createElement(config.label ? 'div' : 'img');
            button.id = config.id;
            button.className = config.className;
            if (config.label) {
                button.innerText = config.label;
            } else {
                button.src = myGame.buttonImages[config.src];
                button.alt = config.alt;
            }

            Object.assign(button.style, config.style);

            if (config.keyCode) {
                button.addEventListener('touchstart', () => triggerButtonEvent(config.keyCode, 'keydown'));
                button.addEventListener('touchend', () => triggerButtonEvent(config.keyCode, 'keyup'));
            } else if (config.action) {
                button.addEventListener('touchstart', config.action);
            }

            buttonsOverlay.appendChild(button);
        });

        function triggerButtonEvent(keyCode, eventType) {
            const keyMap = {
                49: '1',
                53: '5',
                65: 'a',
                68: 'd',
                83: 's',
                70: 'f',
                13: 'Enter'
            };
            const codeMap = {
                49: 'Digit1',
                53: 'Digit5',
                65: 'KeyA',
                68: 'KeyD',
                83: 'KeyS',
                70: 'KeyF',
                13: 'Enter'
            };
            const event = new KeyboardEvent(eventType, {
                key: keyMap[keyCode] || '',
                code: codeMap[keyCode] || '',
                keyCode: keyCode,
                bubbles: true
            });
            canvas.dispatchEvent(event);
        }

        function toggleFullscreen() {
            if (myGame.releaseAllKeys && myGame.updateJoystick) {
                myGame.releaseAllKeys();
                myGame.updateJoystick();
            }
            const elem = document.documentElement;
            if (!document.fullscreenElement && (elem.requestFullscreen || elem.webkitRequestFullscreen || elem.msRequestFullscreen)) {
                if (elem.requestFullscreen) { /* Standard */
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) { /* ipad and mac. Iphone doesn't allow prog fullscreen as of today */
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) { /* IE11 */
                    elem.msRequestFullscreen();
                }
            } else if (document.fullscreenElement) {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
        }
    }

})();