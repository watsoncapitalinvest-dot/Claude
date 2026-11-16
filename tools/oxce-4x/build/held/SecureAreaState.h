#pragma once
/*
 * G.I. Joe: ALL TARGETS NEUTRALIZED - CONTINUE OR EXFILTRATE? (John 16 Nov 00:19, every map)
 * Asked once, the moment the last Cobra goes down. CONTINUE keeps the battle going so the squad can
 * search the map for clues; END TURN then only passes turns, and the ABORT button becomes EXFILTRATE,
 * which ends the mission as a full win (everything carried comes home). EXFILTRATE ends it now.
 */
#include "../Engine/State.h"

namespace OpenXcom
{

class Window;
class Text;
class TextButton;
class SavedBattleGame;
class BattlescapeGame;

class SecureAreaState : public State
{
private:
	Window *_window;
	Text *_txtTitle, *_txtAsk;
	TextButton *_btnContinue, *_btnExfil;
	SavedBattleGame *_save;
	BattlescapeGame *_parent;
public:
	SecureAreaState(SavedBattleGame *save, BattlescapeGame *parent);
	~SecureAreaState() = default;
	void btnContinueClick(Action *action);
	void btnExfilClick(Action *action);
	/// the squad chose CONTINUE: the battle no longer ends on its own
	static bool secured(const SavedBattleGame *save);
	/// push the question if it is due (all Cobra down, squad alive, not asked yet). True if pushed.
	static bool offer(Game *game, SavedBattleGame *save, BattlescapeGame *parent);
};

}
