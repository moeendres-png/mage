# WS211 CURRENT_CONCESSION_CALL_CHAIN (CODE_DERIVED, test-pinned)

Normal client path (any thread, any game moment):

    GUI concede button / network CONCEDE command
      -> GameController.sendPlayerAction(CONCEDE, userId)      [server auth: userPlayerMap]
        -> Game.setConcedingPlayer(ownPlayerId)                [Mage.GameImpl:909]
          -> concedingPlayers queue (+dedup)                   [Mage.GameImpl:914]
          -> signalPlayerConcede(stop?) on priority player     [HumanPlayer:2733]
             (self / self-while-controlling => stop dialog; other => keep going)
          -> checkConcede() if already on game thread          [Mage.GameImpl:954]

Game-thread processing:

    checkConcede()                                             [Mage.GameImpl:960]
      -> leave(playerId)                                       [Mage.GameImpl:3447]
        -> player.leave() (left+loses flags, zones cleared)
        -> checkIfGameIsOver() -> end() + winner               [Mage.GameImpl:978]
        -> 800.4a cleanup (owned out, control effects end,
           stack objects cease, controlled exiled, exile/command sweep)
      (called from checkStateAndTriggered:2404 and post-resolve:1852)

Direct execution seam (tests, bridges, load client):

    Game.concede(playerId)                                     [Mage.GameImpl:1733]
      -> WS211 guard: reject unless canConcede(playerId)
      -> Player.concede(game)                                  [PlayerImpl:2705]
        -> setConcedingPlayer(playerId) + lost(game)

Timeout/quit family (unchanged, distinct from voluntary game concession):

    Player.quit / timerTimeout / idleTimeout -> this.concede(game)
      (PlayerImpl:2681-2702; quit flag set; match-level semantics preserved)

Distinctions preserved: CONCEDE GAME (voluntary, this surface) vs QUIT MATCH
vs IDLE/PRIORITY TIMEOUT vs CONNECTION LOSS (all reuse internals, keep own flags).
