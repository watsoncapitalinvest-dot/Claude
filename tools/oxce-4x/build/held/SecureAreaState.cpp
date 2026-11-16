#include "SecureAreaState.h"
#include "../Engine/Game.h"
#include "../Engine/Options.h"
#include "../Interface/Window.h"
#include "../Interface/Text.h"
#include "../Interface/TextButton.h"
#include "../Savegame/SavedBattleGame.h"
#include "../Mod/Mod.h"
#include "BattlescapeGame.h"
#include "AirFight.h"

namespace OpenXcom
{

SecureAreaState::SecureAreaState(SavedBattleGame *save, BattlescapeGame *parent) : _save(save), _parent(parent)
{
	_screen = false;
	_window = new Window(this, 320, 144, 0, 0);
	_txtTitle = new Text(304, 34, 8, 26);
	_txtAsk = new Text(304, 34, 8, 62);
	_btnContinue = new TextButton(136, 16, 16, 110);
	_btnExfil = new TextButton(136, 16, 168, 110);
	_save->setPaletteByDepth(this);
	add(_window, "messageWindowBorder", "battlescape");
	add(_txtTitle, "messageWindows", "battlescape");
	add(_txtAsk, "messageWindows", "battlescape");
	add(_btnContinue, "messageWindowButtons", "battlescape");
	add(_btnExfil, "messageWindowButtons", "battlescape");
	_window->setHighContrast(true);
	_window->setBackground(_game->getMod()->getSurface("TAC00.SCR"));
	_txtTitle->setBig(); _txtTitle->setHighContrast(true); _txtTitle->setAlign(ALIGN_CENTER); _txtTitle->setWordWrap(true);
	_txtTitle->setText("ALL TARGETS NEUTRALIZED");
	_txtAsk->setHighContrast(true); _txtAsk->setAlign(ALIGN_CENTER); _txtAsk->setWordWrap(true);
	_txtAsk->setText("Continue to search the area, or exfiltrate now? After continuing, ABORT exfiltrates as a win.");
	_btnContinue->setText("CONTINUE"); _btnContinue->setHighContrast(true);
	_btnContinue->onMouseClick((ActionHandler)&SecureAreaState::btnContinueClick);
	_btnContinue->onKeyboardPress((ActionHandler)&SecureAreaState::btnContinueClick, Options::keyCancel);
	_btnExfil->setText("EXFILTRATE"); _btnExfil->setHighContrast(true);
	_btnExfil->onMouseClick((ActionHandler)&SecureAreaState::btnExfilClick);
	_btnExfil->onKeyboardPress((ActionHandler)&SecureAreaState::btnExfilClick, Options::keyOk);
	centerAllSurfaces();
}

void SecureAreaState::btnContinueClick(Action *)
{
	_save->setVanStop("secured", 1);
	_game->popState();
}

void SecureAreaState::btnExfilClick(Action *)
{
	_game->popState();
	_parent->requestEndTurn(false);
}

bool SecureAreaState::secured(const SavedBattleGame *save)
{
	return save && save->getVanStop("secured") != 0;
}

bool SecureAreaState::offer(Game *game, SavedBattleGame *save, BattlescapeGame *parent)
{
	if (!save || !parent || save->isPreview() || save->getVanStop("secAsked")) return false;
	if (save->getObjectiveType() == MUST_DESTROY) return false;
	if (save->getVIPSurvivalPercentage() > 0 && save->getVIPEscapeType() != ESCAPE_NONE) return false;
	if (AirFight::isAirFight(game->getMod(), save)) return false;   // an air or sea fight ends its own way
	BattlescapeTally t = parent->tallyUnits();
	if (t.liveAliens != 0 || t.liveSoldiers <= 0) return false;
	save->setVanStop("secAsked", 1);
	game->pushState(new SecureAreaState(save, parent));
	return true;
}

}
