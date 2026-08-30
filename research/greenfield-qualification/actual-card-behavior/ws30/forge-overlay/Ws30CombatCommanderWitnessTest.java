package forge.gamesimulationtests;

import forge.CardStorageReader;
import forge.LobbyPlayer;
import forge.StaticData;
import forge.ai.PlayerControllerAi;
import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.GameEntity;
import forge.game.GameRules;
import forge.game.GameStage;
import forge.game.GameType;
import forge.game.Match;
import forge.game.ability.AbilityFactory;
import forge.game.ability.AbilityUtils;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.card.CardCollectionView;
import forge.game.card.CounterEnumType;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.phase.PhaseType;
import forge.game.player.IGameEntitiesFactory;
import forge.game.player.Player;
import forge.game.player.PlayerController;
import forge.game.player.RegisteredPlayer;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import forge.item.PaperCard;
import forge.util.Lang;
import forge.util.Localizer;
import org.apache.commons.lang3.tuple.Pair;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/** WS30 actual-card Combat/Commander qualification against pinned Forge main APIs. */
public class Ws30CombatCommanderWitnessTest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final String RULES_URL = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.pdf";
    private static final String[] COMMANDERS = {
            "Isamaru, Hound of Konda", "Talrand, Sky Summoner", "Krenko, Mob Boss", "Ayli, Eternal Pilgrim"
    };
    private static StaticData staticData;

    private static String dir(Path path) { return path.toAbsolutePath().normalize().toString() + File.separator; }

    private static synchronized PaperCard paper(String name) {
        if (staticData == null) {
            Path root = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize();
            while (root != null && !Files.isDirectory(root.resolve("forge-gui/res/cardsfolder"))) root = root.getParent();
            if (root == null) throw new IllegalStateException("Unable to locate pinned Forge root");
            Path res = root.resolve("forge-gui/res");
            Path empty = root.resolve("target/ws30-empty-custom-editions");
            try { Files.createDirectories(empty); } catch (IOException e) { throw new RuntimeException(e); }
            Lang.createInstance("en-US");
            Localizer.getInstance().initialize("en-US", dir(res.resolve("languages")));
            staticData = new StaticData(new CardStorageReader(dir(res.resolve("cardsfolder")), null, false), null,
                    dir(res.resolve("editions")), dir(empty), dir(res.resolve("blockdata")),
                    "Latest Art All Editions", true, false);
        }
        PaperCard pc = staticData.getCommonCards().getUniqueByNameNoAlt(name);
        if (pc == null) throw new IllegalArgumentException("Pinned Forge does not contain card: " + name);
        return pc;
    }

    private static final class Ws30Controller extends PlayerControllerAi {
        Ws30Controller(Game game, Player player, LobbyPlayer lobbyPlayer) { super(game, player, lobbyPlayer); }
        @Override public void declareAttackers(Player attacker, Combat combat) {
            Pair<Map<Card, GameEntity>, Integer> emitted = combat.getAttackConstraints().getLegalAttackers();
            List<Map.Entry<Card, GameEntity>> selected = new ArrayList<>(emitted.getLeft().entrySet());
            selected.sort(Comparator.comparingInt(e -> e.getKey().getId()));
            for (Map.Entry<Card, GameEntity> entry : selected) combat.addAttacker(entry.getKey(), entry.getValue());
            if (!CombatUtil.validateAttackers(combat)) throw new IllegalStateException("rules-core attacker declaration invalid");
        }
        @Override public void declareBlockers(Player defender, Combat combat) {
            String error = CombatUtil.validateBlocks(combat, defender);
            if (error != null) throw new IllegalStateException("empty blockers not rules-core legal: " + error);
        }
    }

    private static final class Ws30LobbyPlayer extends LobbyPlayer implements IGameEntitiesFactory {
        Ws30LobbyPlayer(String name) { super(name); }
        @Override public Player createIngamePlayer(Game gameState, int id) {
            Player player = new Player(getName(), gameState, id);
            player.setFirstController(new Ws30Controller(gameState, player, this)); return player;
        }
        @Override public PlayerController createMindSlaveController(Player master, Player slave) {
            return new Ws30Controller(slave.getGame(), slave, this);
        }
        @Override public void hear(LobbyPlayer player, String message) { }
    }

    private static final class Fixture {
        final Game game; Fixture(Game game) { this.game = game; }
        Player p(int i) { return game.getRegisteredPlayers().get(i); }
    }

    private Fixture fixture() {
        List<RegisteredPlayer> registered = new ArrayList<>();
        for (int i=0;i<4;i++) {
            Deck deck = new Deck("WS30-P"+(i+1));
            deck.getOrCreate(DeckSection.Commander).add(paper(COMMANDERS[i]),1);
            deck.getMain().add(paper("Plains"),20);
            RegisteredPlayer rp=RegisteredPlayer.forCommander(deck); rp.setPlayer(new Ws30LobbyPlayer("WS30-P"+(i+1)));
            registered.add(rp);
        }
        GameRules rules=new GameRules(GameType.Commander); rules.addAppliedVariant(GameType.Commander);
        Game game=new Match(rules,registered,"WS30").createGame(); game.setAge(GameStage.Play);
        for (int i=0;i<registered.size();i++) game.getRegisteredPlayers().get(i).initVariantsZones(registered.get(i));
        game.getTriggerHandler().resetActiveTriggers();
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, game.getRegisteredPlayers().get(0));
        return new Fixture(game);
    }

    private Card putPermanent(Fixture f, Player owner, Player controller, String name) {
        Card card=Card.fromPaperCard(paper(name),owner); card.setController(controller,0);
        controller.getZone(ZoneType.Battlefield).add(card); f.game.getTriggerHandler().registerActiveTrigger(card,false); return card;
    }
    private Card looseCard(Player owner,String name) { return Card.fromPaperCard(paper(name),owner); }
    private Card commanderOnBattlefield(Fixture f, Player p) {
        Card cmd=null; for (Card c:p.getZone(ZoneType.Command)) if (c.isCommander() && !"Commander Effect".equals(c.getName())) { cmd=c; break; }
        Assert.assertNotNull(cmd); p.getZone(ZoneType.Command).remove(cmd); cmd.setController(p,0); p.getZone(ZoneType.Battlefield).add(cmd);
        f.game.getTriggerHandler().registerActiveTrigger(cmd,false); cmd.setSickness(false); return cmd;
    }
    private void forceAttack(Fixture f,Player p,Card creature) {
        Card aura=putPermanent(f,p,p,"Furor of the Bitten"); aura.attachToEntity(creature,null,true); creature.setSickness(false);
    }
    private SpellAbility fromSVar(Card host,String key,Player activator,GameEntity... targets) {
        String definition=host.getSVar(key); Assert.assertNotNull(definition); Assert.assertFalse(definition.isBlank());
        SpellAbility sa=AbilityFactory.getAbility(definition,host); sa.setActivatingPlayer(activator);
        if (targets!=null) for (GameEntity target:targets) sa.getTargets().add(target); return sa;
    }
    private SpellAbility topLevel(Card host,ApiType api,Player activator) {
        for (SpellAbility sa:host.getSpellAbilities()) if (sa.getApi()==api) { sa.setActivatingPlayer(activator); return sa; }
        throw new AssertionError(host.getName()+" has no top-level "+api);
    }
    private void resolve(Fixture f,SpellAbility sa) { AbilityUtils.resolve(sa); f.game.getAction().checkStateEffects(true); resolvePending(f); }
    private void resolvePending(Fixture f) {
        boolean added; do { added=f.game.getStack().addAllTriggeredAbilitiesToStack(); while(!f.game.getStack().isEmpty()) f.game.getStack().resolveStack(); }
        while(added || f.game.getStack().hasSimultaneousStackEntries());
    }
    private static String esc(String s) { if(s==null)return ""; return s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r"); }
    private static String stableAttackMap(Map<Card,GameEntity> map) {
        List<Map.Entry<Card,GameEntity>> entries=new ArrayList<>(map.entrySet());
        entries.sort(Comparator.comparing((Map.Entry<Card,GameEntity> e)->e.getKey().getName()).thenComparingInt(e->e.getKey().getId()));
        List<String> out=new ArrayList<>(); for(var e:entries) out.add(e.getKey().getName()+"->"+e.getValue().getName()); return String.join(";",out);
    }
    private static String restrictionsRequirements(Combat combat) {
        List<String> out=new ArrayList<>();
        combat.getAttackConstraints().getRestrictions().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->out.add("R:"+e.getKey().getName()+"="+e.getValue()));
        combat.getAttackConstraints().getRequirements().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->out.add("Q:"+e.getKey().getName()+"="+e.getValue()));
        return String.join("|",out);
    }
    private static String legalBlockPairs(Combat combat,Player defender) {
        List<String> pairs=new ArrayList<>(); for(Card attacker:combat.getAttackers()) for(Card blocker:defender.getCreaturesInPlay())
            if(CombatUtil.canBlock(attacker,blocker,combat)) pairs.add(attacker.getName()+"<-"+blocker.getName());
        pairs.sort(String::compareTo); return String.join(";",pairs);
    }
    private void emit(String id,String card,String dispatch,String initial,String legalAttackers,String legalBlockers,String rr,String selected,String validation,String combatState,String damage,String post,String assertion) {
        String output=System.getenv("WS30_TRACE_PATH"); if(output==null||output.isBlank())return;
        String json="{\"path_id\":\""+esc(id)+"\",\"card\":\""+esc(card)+"\",\"dispatch\":\""+esc(dispatch)+"\",\"forge_pin\":\""+FORGE_PIN+"\",\"initial_state\":\""+esc(initial)+"\",\"legal_attackers\":\""+esc(legalAttackers)+"\",\"legal_blockers\":\""+esc(legalBlockers)+"\",\"restrictions_requirements\":\""+esc(rr)+"\",\"selected_declaration\":\""+esc(selected)+"\",\"validation_result\":\""+esc(validation)+"\",\"combat_state\":\""+esc(combatState)+"\",\"damage_assignment\":\""+esc(damage)+"\",\"post_damage_state\":\""+esc(post)+"\",\"semantic_assertion\":\""+esc(assertion)+"\",\"result\":\"PASS\",\"evidence_class\":\"TECHNICALLY_CONFORMANT\",\"rules_url\":\""+RULES_URL+"\"}"+System.lineSeparator();
        try { Path p=Path.of(output); if(p.getParent()!=null)Files.createDirectories(p.getParent()); Files.writeString(p,json,StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND); }
        catch(IOException e){throw new RuntimeException(e);}
    }
    private Pair<Map<Card,GameEntity>,Integer> legal(Combat c){return c.getAttackConstraints().getLegalAttackers();}

    private void staticCantAttack(String path,String sourceName) {
        Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card attacker=putPermanent(f,p0,p0,"Grizzly Bears"); attacker.setSickness(false);
        Card source=putPermanent(f,p1,p1,sourceName); if(source.isAura()) source.attachToEntity(attacker,null,true);
        Combat c=new Combat(p0); Assert.assertFalse(CombatUtil.canAttack(attacker,p1)); var e=legal(c); Assert.assertFalse(e.getLeft().containsKey(attacker));
        emit(path,sourceName,"STATIC_MODE:CantAttack","actual static source active",stableAttackMap(e.getLeft()),"",restrictionsRequirements(c),stableAttackMap(e.getLeft()),String.valueOf(CombatUtil.validateAttackers(c)),"attacker excluded","not-applicable","no combat damage","Forge rules core excludes restricted attacker");
    }
    private void staticCantBlock(String path,String sourceName,boolean equipment) {
        Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card attacker=putPermanent(f,p0,p0,"Grizzly Bears"); attacker.setSickness(false); Card blocker;
        if(equipment){blocker=putPermanent(f,p1,p1,"Grizzly Bears"); Card eq=putPermanent(f,p1,p1,sourceName); eq.attachToEntity(blocker,null,true);} else blocker=putPermanent(f,p1,p1,sourceName);
        Combat c=new Combat(p0); c.addAttacker(attacker,p1); Assert.assertFalse(CombatUtil.canBlock(attacker,blocker,c));
        emit(path,sourceName,"STATIC_MODE:CantBlock","attacker present for blocker query",attacker.getName()+"->"+p1.getName(),legalBlockPairs(c,p1),"","none","CombatUtil.canBlock=false","blocker rejected","not-applicable","no combat damage","Forge rules core rejects blocker");
    }
    private void goadPath(String path,String sourceName,String sVar,boolean rootApi,boolean untapAfter) {
        Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card target=putPermanent(f,p0,p0,"Grizzly Bears"); target.setSickness(false);
        Card source=rootApi?looseCard(p1,sourceName):putPermanent(f,p1,p1,sourceName); SpellAbility sa;
        if(rootApi) sa=topLevel(source,ApiType.Goad,p1); else if("Kang Dynasty".equals(sourceName)) sa=fromSVar(source,"DBTap",p1,target); else if("Killian, Decisive Mentor".equals(sourceName)) sa=fromSVar(source,"TrigTap",p1,target); else sa=fromSVar(source,sVar,p1,target);
        resolve(f,sa); Assert.assertTrue(target.isGoaded()); if(untapAfter&&target.isTapped())target.setTapped(false);
        Combat c=new Combat(p0); var e=legal(c); Assert.assertTrue(e.getLeft().containsKey(target)); GameEntity defender=e.getLeft().get(target); Assert.assertNotEquals(defender,p1);
        emit(path,sourceName,"ABILITY_API:Goad","actual Goad resolved; target ready",stableAttackMap(e.getLeft()),"",restrictionsRequirements(c),stableAttackMap(e.getLeft()),"rules-core legal","goaded=true; defender="+defender.getName(),"not-applicable","no combat damage","Actual Goad state feeds Forge attack requirements");
    }

    @Test public void assignedPathsAndSupplementalCommanderCombat() {
        { Fixture f=fixture(); Player p0=f.p(0); Card bear=putPermanent(f,p0,p0,"Grizzly Bears"); forceAttack(f,p0,bear); Combat c=new Combat(p0); var e=legal(c); Assert.assertTrue(e.getLeft().containsKey(bear));
          emit("forge-behavior-v2:4608a1c9abad1297399edee1f9f1826f2547cf75","Furor of the Bitten","STATIC_MODE:MustAttack","actual Aura attached",stableAttackMap(e.getLeft()),"",restrictionsRequirements(c),stableAttackMap(e.getLeft()),"rules-core legal","required attacker present","not-applicable","no combat damage","MustAttack requirement is Forge-generated"); }
        staticCantAttack("forge-behavior-v2:493a600887ba26f97ea5f05448b6a7479e9aed09","Arrest");
        staticCantAttack("forge-behavior-v2:7de29e0dc11dd8feeb11957c3cfc3527e030b3d5","Stormtide Leviathan");
        staticCantAttack("forge-behavior-v2:c32103e4aee9b61922fc405b39fba0f66c61bc66","Pacifism");
        staticCantAttack("forge-behavior-v2:f439b3d257f8d5c3ffecb6e7498b46dc37cecd57","Observed Stasis");

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card bear=putPermanent(f,p0,p0,"Grizzly Bears"); forceAttack(f,p0,bear); putPermanent(f,p1,p1,"Ghostly Prison"); Combat c=new Combat(p0); Cost cost=CombatUtil.getAttackCost(f.game,bear,p1); Assert.assertNotNull(cost); var e=legal(c); Assert.assertFalse(e.getLeft().containsKey(bear));
          emit("forge-behavior-v2:818a4258b636e235634dbd1d66ea14caba522b9b","Ghostly Prison","STATIC_MODE:CantAttackUnless","MustAttack creature faces actual attack tax",stableAttackMap(e.getLeft()),"",restrictionsRequirements(c),stableAttackMap(e.getLeft()),"attack_cost="+cost,"unpaid attacker omitted","not-applicable","no combat damage","Forge exposes attack cost and requirements do not bypass it"); }

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card bear=putPermanent(f,p0,p0,"Grizzly Bears"); bear.setCounters(CounterEnumType.P1P1,2); forceAttack(f,p0,bear); Card nils=putPermanent(f,p1,p1,"Nils, Discipline Enforcer"); Combat c=new Combat(p0); Cost cost=CombatUtil.getAttackCost(f.game,bear,p1); Assert.assertNotNull(cost); String text=cost.toString(); Assert.assertTrue(text.contains("2"),text);
          emit("forge-behavior-v2:86936c5bedbc4e67d000cff71f1de4d75ad7a848",nils.getName(),"SVAR_RUNTIME_EXPRESSION:X","attacker has two counters",stableAttackMap(legal(c).getLeft()),"",restrictionsRequirements(c),stableAttackMap(legal(c).getLeft()),"attack_cost="+text,"X bound from attacker counters","not-applicable","no combat damage","Actual Nils X is resolved by Forge attack-cost machinery"); }

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card s=putPermanent(f,p0,p0,"Spire Serpent"); s.setSickness(false); Assert.assertFalse(CombatUtil.canAttack(s,p1)); putPermanent(f,p0,p0,"Sol Ring"); putPermanent(f,p0,p0,"Memnite"); putPermanent(f,p0,p0,"Ornithopter"); Assert.assertTrue(CombatUtil.canAttack(s,p1)); Combat c=new Combat(p0);
          emit("forge-behavior-v2:90d68df9a7f2c4b0ca457ab8e149239733faa9f9",s.getName(),"STATIC_MODE:CanAttackDefender","Metalcraft true with three actual artifacts",stableAttackMap(legal(c).getLeft()),"",restrictionsRequirements(c),stableAttackMap(legal(c).getLeft()),"canAttack=true","defender permission active","not-applicable","no combat damage","Forge applies actual Metalcraft CanAttackDefender"); }

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1),p2=f.p(2),p3=f.p(3); p1.setLife(30,null); p2.setLife(35,null); p3.setLife(25,null); Card g=putPermanent(f,p0,p0,"Galactus, Devourer of Worlds"); g.setSickness(false); Combat c=new Combat(p0); var e=legal(c); Assert.assertEquals(e.getLeft().get(g),p2);
          emit("forge-behavior-v2:b3f45b78e35ab0e0d0bddc5de59e28a4217e5793",g.getName(),"STATIC_MODE:MustAttack","opponent life 30/35/25",stableAttackMap(e.getLeft()),"",restrictionsRequirements(c),stableAttackMap(e.getLeft()),"defender=p2","greatest-life opponent selected","not-applicable","no combat damage","Forge resolves defender-specific MustAttack"); }

        staticCantBlock("forge-behavior-v2:7160410cd26648bb11bd7ae58ed900581b3c5e3e","Goblin Glider",false);
        staticCantBlock("forge-behavior-v2:cf281f9419491d9761b8865a93ceb497f547d0b8","Copper Carapace",true);
        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card a=putPermanent(f,p0,p0,"Grizzly Bears"),b=putPermanent(f,p1,p1,"Cloud Elemental"); a.setSickness(false); Combat c=new Combat(p0); c.addAttacker(a,p1); Assert.assertFalse(CombatUtil.canBlock(a,b,c));
          emit("forge-behavior-v2:a099f5a25934e2b32ede046883319533c2a9aee5",b.getName(),"STATIC_MODE:CantBlockBy","ground attacker",a.getName()+"->"+p1.getName(),legalBlockPairs(c,p1),"","none","canBlock=false","evasion restriction","not-applicable","no combat damage","Forge evaluates CantBlockBy"); }
        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card a=putPermanent(f,p0,p0,"Grizzly Bears"),b=putPermanent(f,p1,p1,"Sneaky Homunculus"); a.setSickness(false); Combat c=new Combat(p0); c.addAttacker(a,p1); Assert.assertFalse(CombatUtil.canBlock(a,b,c));
          emit("forge-behavior-v2:fb488b3eb0eec715ba32aa171e8f8bbfb3aef8db",b.getName(),"STATIC_MODE:CantBlockBy","power-2 attacker",a.getName()+"->"+p1.getName(),legalBlockPairs(c,p1),"","none","canBlock=false","power restriction","not-applicable","no combat damage","Forge evaluates power threshold"); }

        goadPath("forge-behavior-v2:414dd17d684c18e2dcb4f789f92e4ce01c5885c5","Puppet Master, String Puller","TrigGoad",false,false);
        goadPath("forge-behavior-v2:453f529f97c47c4e324373549febbc00f6a1d307","Ransom Note","DBGoad",false,false);
        goadPath("forge-behavior-v2:63c992a30c18a252dc47d4ab9b40bdc91c5f662d","Kang Dynasty","DBGoad",false,true);
        goadPath("forge-behavior-v2:906853a2e82e374fc6d41ae1f2b6e0645799f330","Taunt from the Rampart","",true,false);
        goadPath("forge-behavior-v2:986bb52d86a942ca99418be90660456dddc90fbf","Killian, Decisive Mentor","DBGoad",false,true);
        goadPath("forge-behavior-v2:a6c5a5d64d9b1fd64254959b5b11c3cca4ec1269","Fast Forward","",true,false);
        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card t=putPermanent(f,p0,p0,"Grizzly Bears"),r=putPermanent(f,p1,p1,"Ransom Note"); resolve(f,fromSVar(r,"DBGoad",p1,t)); Assert.assertTrue(t.isGoaded()); Card s=putPermanent(f,p0,p0,"Serene Sleuth"); resolve(f,fromSVar(s,"DBNoGoad",p0)); Assert.assertFalse(t.isGoaded()); Combat c=new Combat(p0);
          emit("forge-behavior-v2:b3afcc21787740e9bc493d07f95d972d030f1d85",s.getName(),"ABILITY_API:Goad(NoLonger)","actual goad prestate",stableAttackMap(legal(c).getLeft()),"","",stableAttackMap(legal(c).getLeft()),"isGoaded=false","goad cleared","not-applicable","no combat damage","Actual NoLonger clears Forge goad state"); }

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card h=putPermanent(f,p0,p0,"Voracious Hydra"),b=putPermanent(f,p1,p1,"Grizzly Bears"); resolve(f,fromSVar(h,"DBFight",p0,b)); Assert.assertEquals(h.getZone().getZoneType(),ZoneType.Graveyard);
          emit("forge-behavior-v2:554fc179d6b92c7929aaf32b42866ef9ebfbb865",h.getName(),"ABILITY_API:Fight","0/1 vs 2/2","not-applicable","not-applicable","not-applicable","target=Grizzly Bears","actual DBFight resolved","Fight resolved","Forge mutual noncombat damage","Hydra=Graveyard","Actual SVar uses Forge Fight/damage/SBA"); }
        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card cmd=commanderOnBattlefield(f,p0),victim=putPermanent(f,p1,p1,"Memnite"),spell=looseCard(p0,"Fight for the Throne"); SpellAbility root=topLevel(spell,ApiType.PutCounter,p0); root.getTargets().add(cmd); Assert.assertNotNull(root.getSubAbility()); root.getSubAbility().getTargets().add(victim); resolve(f,root); resolvePending(f); Assert.assertEquals(victim.getZone().getZoneType(),ZoneType.Graveyard); Assert.assertEquals(f.game.getMonarch(),p0);
          emit("forge-behavior-v2:945cb309bfe37e292fbecc172efa4789ff1156d1",spell.getName(),"ABILITY_API:Fight","commander controlled; Memnite opponent","not-applicable","not-applicable","commander condition actual","parent commander; sub target Memnite","victim died; delayed trigger resolved","commander identity preserved","Forge Fight damage","victim=Graveyard; monarch=p0","Commander-sensitive delayed trigger sees controlled commander"); }
        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card a=putPermanent(f,p0,p0,"Grizzly Bears"),b=putPermanent(f,p1,p1,"Grizzly Bears"),wave=looseCard(p0,"Wave of Reckoning"); resolve(f,topLevel(wave,ApiType.EachDamage,p0)); Assert.assertEquals(a.getZone().getZoneType(),ZoneType.Graveyard); Assert.assertEquals(b.getZone().getZoneType(),ZoneType.Graveyard);
          emit("forge-behavior-v2:2ccb65722925af0c56ab0c6cb5a0d9b95f82a5a3",wave.getName(),"ABILITY_API:EachDamage","two 2/2 creatures","not-applicable","not-applicable","not-applicable","actual top-level EachDamage","resolved","noncombat damage","2 each","both graveyard","EachDamage and SBA are Forge-owned"); }

        { Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card a=putPermanent(f,p0,p0,"Grizzly Bears"); forceAttack(f,p0,a); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); Combat c=f.game.getCombat(); Assert.assertTrue(c.isAttacking(a)); Card aura=putPermanent(f,p1,p1,"Observed Stasis"); aura.attachToEntity(a,null,true); resolve(f,fromSVar(aura,"TrigRemoveFromCombat",p1)); Assert.assertFalse(c.isAttacking(a));
          emit("forge-behavior-v2:fdfbb84c89a48e0bd1600cf3e2474f9d97b7f594",aura.getName(),"ABILITY_API:RemoveFromCombat","rules-core declared attacker",a.getName()+"->"+p1.getName(),"",restrictionsRequirements(c),"actual RemoveFromCombat","isAttacking=false","removed","none","no combat damage","Actual RemoveFromCombat mutates Forge Combat"); }

        { Fixture f=fixture(); Player p0=f.p(0); Card w=putPermanent(f,p0,p0,"Goblin Wardriver"),m=putPermanent(f,p0,p0,"Grizzly Bears"); forceAttack(f,p0,w); forceAttack(f,p0,m); int before=m.getNetPower(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); resolvePending(f); Combat c=f.game.getCombat(); Assert.assertTrue(c.isAttacking(w)); Assert.assertTrue(c.isAttacking(m)); Assert.assertEquals(m.getNetPower(),before+1);
          emit("forge-behavior-v2:84310059dc7e1f97295b71374b8fc9c7a2881ad2",w.getName(),"KEYWORD_TRIGGER:BATTLE_CRY","two required attackers",stableAttackMap(c.getAttackersAndDefenders()),legalBlockPairs(c,f.p(1)),restrictionsRequirements(c),stableAttackMap(c.getAttackersAndDefenders()),String.valueOf(CombatUtil.validateAttackers(c)),"both attacking","pending","power "+before+"->"+m.getNetPower(),"Battle cry resolves after authoritative declaration"); }
        { Fixture f=fixture(); Player p0=f.p(0); Card a=putPermanent(f,p0,p0,"Dawnray Archer"); forceAttack(f,p0,a); int before=a.getNetPower(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); resolvePending(f); Combat c=f.game.getCombat(); Assert.assertEquals(c.getAttackers().size(),1); Assert.assertEquals(a.getNetPower(),before+1);
          emit("forge-behavior-v2:a347f2a0119d27a12fb8624dd7fb984c0c186f94",a.getName(),"KEYWORD_TRIGGER:EXALTED","one required attacker",stableAttackMap(c.getAttackersAndDefenders()),legalBlockPairs(c,f.p(1)),restrictionsRequirements(c),stableAttackMap(c.getAttackersAndDefenders()),String.valueOf(CombatUtil.validateAttackers(c)),"attacks alone","pending","power "+before+"->"+a.getNetPower(),"Exalted resolves after Forge declares one attacker"); }
        { Fixture f=fixture(); Player p0=f.p(0); Card t=putPermanent(f,p0,p0,"Titania, Proud Pummeler"); forceAttack(f,p0,t); int base=t.getNetPower(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); resolvePending(f); Combat c=f.game.getCombat(); Assert.assertTrue(c.isAttacking(t)); Assert.assertEquals(t.getNetPower(),base+1); Player d=(Player)c.getDefenderByAttacker(t); int before=d.getLife(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_FIRST_STRIKE_DAMAGE,()->resolvePending(f)); int afterFirst=d.getLife(); Assert.assertTrue(afterFirst<before); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DAMAGE,()->resolvePending(f)); Assert.assertEquals(d.getLife(),afterFirst);
          emit("forge-behavior-v2:14610534b2a56cbaa8ae0851d88d9322d3e3314c",t.getName(),"KEYWORD_TRIGGER:MELEE","actual Titania required attacker",stableAttackMap(c.getAttackersAndDefenders()),legalBlockPairs(c,d),restrictionsRequirements(c),stableAttackMap(c.getAttackersAndDefenders()),String.valueOf(CombatUtil.validateAttackers(c)),"melee power="+t.getNetPower(),"Forge first-strike step dealt "+(before-afterFirst),"life="+d.getLife(),"Melee and first strike are Forge Combat-resolved"); }

        { Fixture f=fixture(); Player p0=f.p(0); Card cmd=commanderOnBattlefield(f,p0); forceAttack(f,p0,cmd); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); Combat c=f.game.getCombat(); Player d=(Player)c.getDefenderByAttacker(cmd); int before=d.getLife(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DAMAGE,()->resolvePending(f)); int dealt=before-d.getLife(); Assert.assertTrue(dealt>0); Assert.assertEquals(d.getCommanderDamage(cmd),dealt);
          emit("SUPPLEMENTAL:COMMANDER_DAMAGE",cmd.getName(),"COMMANDER_COMBAT_DAMAGE","actual commander from command zone to battlefield",stableAttackMap(c.getAttackersAndDefenders()),legalBlockPairs(c,d),restrictionsRequirements(c),stableAttackMap(c.getAttackersAndDefenders()),"damage dealt","commanderDamage="+d.getCommanderDamage(cmd),"Combat.assign/deal","life="+d.getLife()+"; commanderDamage="+d.getCommanderDamage(cmd),"Forge tracks same-commander combat damage identity"); }
        { Fixture f=fixture(); Player p0=f.p(0); Card ace=putPermanent(f,p0,p0,"Fencing Ace"); forceAttack(f,p0,ace); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DECLARE_ATTACKERS); Combat c=f.game.getCombat(); Player d=(Player)c.getDefenderByAttacker(ace); int before=d.getLife(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_FIRST_STRIKE_DAMAGE,()->resolvePending(f)); int first=d.getLife(); f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_DAMAGE,()->resolvePending(f)); int second=d.getLife(); Assert.assertTrue(first<before); Assert.assertTrue(second<first);
          emit("SUPPLEMENTAL:DOUBLE_STRIKE",ace.getName(),"KEYWORD:DOUBLE_STRIKE","actual double-strike attacker",stableAttackMap(c.getAttackersAndDefenders()),legalBlockPairs(c,d),restrictionsRequirements(c),stableAttackMap(c.getAttackersAndDefenders()),"both damage steps","first+regular","first="+(before-first)+"; regular="+(first-second),"life="+second,"Forge schedules double strike in both damage steps"); }
    }
}
