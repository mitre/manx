<script setup>
import { inject, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";

const $api = inject("$api");

onMounted(async () => {});
</script>

<style scoped>
@import "/manx/static/css/basic.css";
@import "/manx/static/css/xterm.css";
</style>

<script>
import '/manx/static/js/terminal.js"';

export default {
    inject: ["$api"],
    data() {
        return {
            DEFAULT_EXECUTORS: ['sh'],
            DEFAULT_PLATFORM: 'darwin',

            sessions: JSON.parse('{{ sessions | tojson }}'),
            tactics: [],
            techniques: [],
            procedures: [],
            selectedSessionID: '',
            selectedTacticName: '',
            selectedTechniqueID: '',
            selectedProcedureID: '',
            terminalCommand: '',

            get sessionIDs() {
                return this.sessions ? this.sessions.flatMap((s) => s.id) : [];
            },

            get selectedSession() {
                return this.sessions ? (this.sessions.find((s) => s.id.toString() === this.selectedSessionID.toString())) : null;
            },
        }
    },
    created() {
        this.initPage();
  },
  methods: {
    async initPage() {
        while (this.$refs.header) {
            if (!document.querySelector('.xterm-cursor-layer') && window.loadManxTerm) {
                window.loadManxTerm();
            }
            await sleep(3000);
            this.refreshManx();
        }
    },

    refreshManx() {
        this.$api.post('/plugin/manx/sessions').then((sessions) => {
            // Join new manx agents in array, and assign default platform and executors if DNE
            this.sessions = this.sessions.concat(sessions.map((s) => ({ ...s, platform: s.platform || this.DEFAULT_PLATFORM, executors: s.executors || [this.DEFAULT_EXECUTORS] })).filter((s) => !this.sessionIDs.includes(s.id)));
        }).catch((error) => {
            toast('Error refreshing manx', false);
            console.error(error);
        });
    },

    resetFields() {
        this.selectedTacticName = '';
        this.selectedTechniqueID = '';
        this.selectedProcedureID = '';
    },

    getTactics() {
        const getUniqueAbilities = (self, data) => {
            if (data.abilities) {
                const seen = [];
                self.tactics = data.abilities.filter((a) => {
                    if (!seen.includes(a.tactic)) {
                        seen.push(a.tactic);
                        return true;
                    }
                    return false;
                });
            }
        };

        restRequest('POST', { paw: this.selectedSession.info }, (data) => {
            getUniqueAbilities(this, data);
        }, '/plugin/manx/ability');
    },

    getTechniques() {
        this.selectedTechniqueID = '';
        this.selectedProcedureID = '';

        let seenIDs = [];
        this.techniques = this.tactics.filter((a) => {
            if (a.tactic === this.selectedTacticName && !seenIDs.includes(a.technique_id)) {
                seenIDs.push(a.technique_id);
                return true;
            }
            return false;
        });
    },

    getProcedures() {
        this.selectedProcedureID = '';

        this.procedures = this.techniques.filter((t) => t.technique_id === this.selectedTechniqueID);
    },

    getProcedure() {
        const getCommands = (self, data) => {
            if (data && data.length > 0) {
                data = JSON.parse(data);
                data.forEach((ability) => {
                    const executor = ability.executors.find((e) => e.platform === self.selectedSession.platform && e.name === self.selectedSession.executors[0]);
                    self.terminalCommand = executor ? executor.command : '';
                });
            } else toast('No ability available for this agent\'s platform and executor combination');
        };
        restRequest('POST', {
            index: 'abilities',
            ability_id: this.selectedProcedureID
        }, (data) => {
            getCommands(this, data);
        });
    }
  }
}
</script>

<template lang="pug">
#manxPage(v-cloak @watch-selectedSessionID="resetFields")
  div(ref="header")
    h2 Manx
    p.has-text-weight-bold A coordinated access trojan (CAT)
    p
      | The Manx agent, written in GoLang, connects to the server over the TCP 
      i contact point
      | . This raw TCP socket connection allows Manx to keep a persistent connection between host-and-server. Bundled with Manx is a reverse-shell management tool, called the 
      i terminal
      | - below - which allows you to establish a local shell on an agent.
    p.has-text-weight-bold To deploy a Manx agent, go to the Agents tab.
  hr
  .is-flex.is-flex-direction-column
    h3 Terminal
    .is-flex.is-flex-direction-row.is-justify-content-space-around.mb-5
      .select.is-small
        select#session-id(v-model="selectedSessionID" @change="getTactics")
          option(value="" disabled selected) Select a session
          template(v-for="s in sessions" :key="s.id")
            option(:value="s.id" :data-paw="s.info" :data-platform="s.platform" :data-executor="s.executors ? s.executors[0] : 'sh'" v-text="s.id + ' - ' + s.info")
      .select.is-small
        select(v-model="selectedTacticName" id="tactic-filter" @change="getTechniques")
          option(value="" disabled selected) Select a tactic
          template(v-for="a in tactics" :key="a.ability_id")
            option(v-text="a.tactic")
      .select.is-small
        select(v-model="selectedTechniqueID" @change="getProcedures")
          option(value="" disabled selected) Select a technique
          template(v-for="t in techniques" :key="t.technique_id")
            option(:value="t.technique_id" v-text="t.technique_id + ' | ' + t.technique_name")
      .select.is-small
        select#procedure-filter(v-model="selectedProcedureID" @change="getProcedure")
          option(value="" disabled selected) Select a procedure
          template(v-for="p in procedures")
            option(v-text="p.name" :value="p.ability_id")
    div(style="visibility:hidden;position:absolute" id="xterminal-command" v-text="terminalCommand")
    div#xterminal

</template>