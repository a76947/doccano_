<template>
  <v-list dense>
    <v-btn
      color="primary"
      class="ms-4 my-1 mb-2 text-capitalize"
      nuxt
      @click="toLabeling"
    >
      <v-icon left>{{ mdiPlayCircleOutline }}</v-icon>
      {{ $t('home.startAnnotation') }}
    </v-btn>
    <v-list-item-group v-model="selected" mandatory>
      <div v-for="(item, i) in filteredItems" :key="i">
        <!-- Itens normais -->
        <template v-if="item.link !== 'rulesReports'">
          <v-list-item
            @click="$router.push(localePath(`/projects/${$route.params.id}/${item.link}`))"
          >
            <v-list-item-action>
              <v-icon>{{ item.icon }}</v-icon>
            </v-list-item-action>
            <v-list-item-content>
              <v-list-item-title>{{ item.text }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
        <!-- Item de Relatórios (dropdown) -->
        <template v-else>
          <v-expansion-panels flat>
            <v-expansion-panel :key="i">
              <v-expansion-panel-header>
                <v-list-item-action class="pl-0" style="margin-left: -7px;">
                  <v-icon>{{ item.icon }}</v-icon>
                </v-list-item-action>
                <v-list-item-content class="pl-0" style="margin-left: -65px;">
                  <v-list-item-title>{{ item.text }}</v-list-item-title>
                </v-list-item-content>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <v-list-item
                  @click="$router.push(localePath(`/projects/${$route.params.id}/rules/anotacao`))"
                >
                  <v-list-item-title>Relatório de Anotação</v-list-item-title>
                </v-list-item>
                <v-list-item
                  @click="$router.push(
                    localePath(`/projects/${$route.params.id}/rules/annotators`))"
                >
                  <v-list-item-title>Relatório de Anotadores</v-list-item-title>
                </v-list-item>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </template>
      </div>
    </v-list-item-group>
  </v-list>
</template>

<script>
import {
  mdiAccount,
  mdiBookOpenOutline,
  mdiChartBar,
  mdiCog,
  mdiCommentAccountOutline,
  mdiDatabase,
  mdiHome,
  mdiLabel,
  mdiPlayCircleOutline,
  mdiHistory,
  mdiViewDashboard,
  mdiAlertCircleOutline,
  mdiChartPie,
  mdiChartBox
} from '@mdi/js'
import { getLinkToAnnotationPage } from '~/presenter/linkToAnnotationPage'

export default {
  props: {
    isProjectAdmin: {
      type: Boolean,
      default: false,
      required: true
    },
    project: {
      type: Object,
      default: () => ({}),
      required: true
    }
  },
  data() {
    return {
      selected: 0,
      mdiPlayCircleOutline
    }
  },
  computed: {
    filteredItems() {
      const items = [
        {
          icon: mdiHome,
          text: this.$t('projectHome.home'),
          link: '',
          isVisible: true
        },
        {
          icon: mdiDatabase,
          text: this.$t('dataset.dataset'),
          link: 'dataset',
          isVisible: true
        },
        {
          icon: mdiLabel,
          text: this.$t('labels.labels'),
          link: 'labels',
          isVisible:
            (this.isProjectAdmin ||
              this.project.allowMemberToCreateLabelType) &&
            this.project.canDefineLabel
        },
        {
          icon: mdiLabel,
          text: 'Relations',
          link: 'links',
          isVisible:
            (this.isProjectAdmin ||
              this.project.allowMemberToCreateLabelType) &&
            this.project.canDefineRelation
        },
        {
          icon: mdiAccount,
          text: this.$t('members.members'),
          link: 'members',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiCommentAccountOutline,
          text: 'Comments',
          link: 'comments',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiBookOpenOutline,
          text: this.$t('guideline.guideline'),
          link: 'guideline',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiChartBar,
          text: this.$t('statistics.statistics'),
          link: 'metrics',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiViewDashboard,
          text: 'Perspetivas',
          link: 'perspectives',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiDatabase,
          text: 'Perspetivas',
          link: 'perspectives',
          isVisible: !this.isProjectAdmin
        },
        {
          icon: mdiAlertCircleOutline,
          text: 'Discrepâncias',
          link: 'discrepancies',
          isVisible: this.isProjectAdmin
        },
        // Remova os itens individuais e insira o único item dropdown "Relatórios"
        {
          icon: mdiChartBox,
          text: 'Relatórios',
          link: 'rulesReports',
          isVisible: true
        },
        {
          icon: mdiCog,
          text: this.$t('settings.title'),
          link: 'settings',
          isVisible: this.isProjectAdmin
        },
        {
          icon: mdiChartBar,
          text: 'Votações',
          link: 'votacoes',
          isVisible: true
        },
        {
          icon: mdiChartBar,
          text: 'Regras',
          link: 'rules',
          isVisible: true
        },
        {
          icon: mdiHistory,
          text: 'Histórico das Regras',
          link: 'rules/history'
        },
        {
          icon: mdiChartPie,
          text: 'Annotation Distribution',
          link: 'annotation-distribution',
          isVisible: true
        }
      ]
      return items.filter(item => item.isVisible)
    }
  },
  methods: {
    toLabeling() {
      const query = this.$services.option.findOption(this.$route.params.id)
      const link = getLinkToAnnotationPage(
        this.$route.params.id,
        this.project.projectType
      )
      this.$router.push({
        path: this.localePath(link),
        query
      })
    }
  }
}
</script>
