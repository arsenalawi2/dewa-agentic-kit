<template>
  <div class="arch-page">
    <!-- ─── Hero ─── -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-badge">Enterprise Architecture Repository</div>
        <h1 class="hero-title">Project Architecture</h1>
        <p class="hero-sub">
          Every project. Every technology. Every connection.
          A live map of the personal infrastructure that runs the work.
        </p>
        <div class="hero-stats" v-if="data">
          <div class="hero-stat">
            <span class="hero-stat-value">{{ data.projects.length }}</span>
            <span class="hero-stat-label">Projects</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-value">{{ uniqueTechCount }}</span>
            <span class="hero-stat-label">Technologies</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-value">{{ uniqueLanguages.length }}</span>
            <span class="hero-stat-label">Languages</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-value">{{ runningCount }}</span>
            <span class="hero-stat-label">Running Now</span>
          </div>
        </div>
        <a href="#network" class="hero-cta">Explore the Graph &#x2192;</a>
      </div>
    </section>

    <!-- ─── Inventory: Big Project Cards ─── -->
    <section class="section">
      <div class="section-inner wide">
        <div class="section-label">Inventory</div>
        <h2 class="section-title">Every project, every stack</h2>
        <p class="section-desc">
          Each card lists every technology used by a project, grouped by category. Click any technology to expand a detailed breakdown — what it does, how it's used, and which other projects share it.
        </p>

        <div class="category-tabs">
          <button
            v-for="cat in projectCategories"
            :key="cat"
            :class="['category-tab', { active: activeCategory === cat }]"
            @click="activeCategory = cat"
          >
            {{ cat }}
            <span class="category-tab-count">{{ projectsInCategory(cat).length }}</span>
          </button>
          <div class="expand-all-controls">
            <button class="expand-all-btn" @click="expandAllProjects">Expand all</button>
            <button class="expand-all-btn" @click="collapseAllProjects">Collapse all</button>
          </div>
        </div>

        <div class="project-grid-big" v-if="data">
          <div
            v-for="proj in filteredProjects"
            :key="proj.id"
            class="project-card-big"
            :class="{ 'is-running': proj.status === 'running', 'is-collapsed': !expandedProjects.has(proj.id) }"
          >
            <!-- Clickable header (always visible) -->
            <button class="big-card-header-btn" @click="toggleProject(proj.id)">
              <svg
                class="card-chevron"
                :class="{ open: expandedProjects.has(proj.id) }"
                width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round"
              >
                <polyline points="9 6 15 12 9 18"/>
              </svg>
              <div class="big-card-header-content">
                <div class="big-card-title-row">
                  <h3 class="big-card-title">{{ proj.name }}</h3>
                  <span :class="['big-card-status', `status-${proj.status.replace(/\s/g, '-')}`]">
                    {{ proj.status }}
                  </span>
                </div>
                <div class="big-card-meta-row">
                  <span class="big-card-meta-item">{{ proj.category }}</span>
                  <span class="big-card-meta-sep">·</span>
                  <span class="big-card-meta-item">{{ flattenStack(proj.stack).length }} technologies</span>
                  <span class="big-card-meta-sep" v-if="Object.keys(proj.ports).length">·</span>
                  <span class="big-card-meta-item" v-if="Object.keys(proj.ports).length">
                    {{ Object.keys(proj.ports).length }} port{{ Object.keys(proj.ports).length === 1 ? '' : 's' }}
                  </span>
                  <span class="big-card-path-inline">{{ proj.path }}</span>
                </div>
              </div>
            </button>

            <!-- Body: only when expanded -->
            <transition name="card-expand">
            <div v-if="expandedProjects.has(proj.id)" class="big-card-body">
            <div class="big-card-header">
              <p class="big-card-purpose">{{ proj.purpose }}</p>
              <div class="big-card-ports" v-if="Object.keys(proj.ports).length">
                <span
                  v-for="(port, key) in proj.ports"
                  :key="key"
                  class="port-pill"
                >
                  {{ key }}: {{ port }}
                </span>
              </div>
            </div>

            <!-- Stack groups: each group has clickable items -->
            <div class="big-stack-grid">
              <div
                v-for="(items, cat) in nonEmptyStack(proj.stack)"
                :key="cat"
                class="big-stack-group"
              >
                <h4
                  class="big-stack-heading"
                  :style="{ borderColor: data.categories[cat]?.color }"
                >
                  {{ data.categories[cat]?.label || cat }}
                </h4>
                <div class="big-stack-items">
                  <button
                    v-for="item in items"
                    :key="item"
                    class="big-stack-item"
                    :class="{ active: expandedTech === item && expandedFromProject === proj.id }"
                    @click="toggleTechDetail(item, proj.id)"
                  >
                    <span class="big-stack-item-text">{{ item }}</span>
                    <svg
                      class="big-stack-chevron"
                      width="11" height="11" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" stroke-width="2.5"
                      stroke-linecap="round" stroke-linejoin="round"
                    >
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Inline expanded tech detail (per-card) -->
            <transition name="tech-expand">
              <div
                v-if="expandedFromProject === proj.id && expandedTechDetail"
                class="tech-detail"
              >
                <div class="tech-detail-header">
                  <h3 class="tech-detail-title">{{ expandedTechDetail.name }}</h3>
                  <span class="tech-detail-role">{{ expandedTechDetail.role }}</span>
                  <button class="tech-detail-close" @click="expandedTech = null; expandedFromProject = null">×</button>
                </div>
                <p class="tech-detail-desc">{{ expandedTechDetail.desc }}</p>

                <!-- Enterprise-level structured fields -->
                <div class="tech-detail-grid">
                  <div v-if="expandedTechDetail.vendor" class="tech-field">
                    <div class="tech-field-label">Vendor</div>
                    <div class="tech-field-value">{{ expandedTechDetail.vendor }}</div>
                  </div>
                  <div v-if="expandedTechDetail.license" class="tech-field">
                    <div class="tech-field-label">License</div>
                    <div class="tech-field-value">{{ expandedTechDetail.license }}</div>
                  </div>
                  <div v-if="expandedTechDetail.maturity" class="tech-field">
                    <div class="tech-field-label">Maturity</div>
                    <div class="tech-field-value">
                      <span :class="['maturity-pill', `maturity-${expandedTechDetail.maturity.toLowerCase().replace(/\s/g, '-')}`]">
                        {{ expandedTechDetail.maturity }}
                      </span>
                    </div>
                  </div>
                  <div v-if="expandedTechDetail.cost" class="tech-field">
                    <div class="tech-field-label">Cost Model</div>
                    <div class="tech-field-value">{{ expandedTechDetail.cost }}</div>
                  </div>
                  <div v-if="expandedTechDetail.lockInRisk" class="tech-field">
                    <div class="tech-field-label">Lock-in Risk</div>
                    <div class="tech-field-value">
                      <span :class="['risk-pill', `risk-${expandedTechDetail.lockInRisk.toLowerCase().replace(/\s/g, '-')}`]">
                        {{ expandedTechDetail.lockInRisk }}
                      </span>
                    </div>
                  </div>
                  <div v-if="expandedTechDetail.adoptionStatus" class="tech-field">
                    <div class="tech-field-label">Adoption Status</div>
                    <div class="tech-field-value">{{ expandedTechDetail.adoptionStatus }}</div>
                  </div>
                </div>

                <div v-if="expandedTechDetail.specs?.length" class="tech-detail-specs">
                  <div v-for="spec in expandedTechDetail.specs" :key="spec.label" class="tech-spec">
                    <span class="tech-spec-label">{{ spec.label }}</span>
                    <span class="tech-spec-value">{{ spec.value }}</span>
                  </div>
                </div>

                <div v-if="expandedTechDetail.alternatives?.length" class="tech-detail-usage">
                  <span class="tech-usage-label">Alternatives we could swap to</span>
                  <div class="tech-usage-tags">
                    <span v-for="t in expandedTechDetail.alternatives" :key="t" class="tech-usage-tag">{{ t }}</span>
                  </div>
                </div>

                <div v-if="expandedTechDetail.dependsOn?.length" class="tech-detail-usage">
                  <span class="tech-usage-label">Depends on</span>
                  <div class="tech-usage-tags">
                    <span v-for="t in expandedTechDetail.dependsOn" :key="t" class="tech-usage-tag">{{ t }}</span>
                  </div>
                </div>

                <div class="tech-detail-usage">
                  <span class="tech-usage-label">Used by {{ expandedTechDetail.projects.length }} project{{ expandedTechDetail.projects.length === 1 ? '' : 's' }} in this stack</span>
                  <div class="tech-usage-tags">
                    <span
                      v-for="pid in expandedTechDetail.projects"
                      :key="pid"
                      class="tech-usage-tag"
                    >
                      {{ projectName(pid) }}
                    </span>
                  </div>
                </div>

                <div v-if="expandedTechDetail.usedFor?.length" class="tech-detail-usage">
                  <span class="tech-usage-label">What it does in this stack</span>
                  <div class="tech-usage-tags">
                    <span v-for="t in expandedTechDetail.usedFor" :key="t" class="tech-usage-tag tech-usage-tag-purpose">{{ t }}</span>
                  </div>
                </div>

                <div v-if="expandedTechDetail.docs" class="tech-detail-footer">
                  <a :href="expandedTechDetail.docs" target="_blank" rel="noopener" class="tech-detail-link">
                    Official docs &#x2192;
                  </a>
                </div>
              </div>
            </transition>
            </div>
            </transition>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Shared Tech Grid ─── -->
    <section class="section section-alt">
      <div class="section-inner wide">
        <div class="section-label">Shared Technology</div>
        <h2 class="section-title">What spans the most projects</h2>
        <p class="section-desc">
          Technologies sorted by how many projects depend on them. The most-used ones are the foundation; the long tail is project-specific. Click any to expand its details above.
        </p>

        <div class="shared-grid">
          <div
            v-for="entry in topSharedTech"
            :key="entry.name"
            class="shared-card"
            @click="toggleTechDetail(entry.name); scrollToTechDetail()"
          >
            <div class="shared-card-top">
              <span
                class="shared-card-dot"
                :style="{ background: entry.color }"
              ></span>
              <span class="shared-card-name">{{ entry.name }}</span>
              <span class="shared-card-count">{{ entry.projects.length }}</span>
            </div>
            <div class="shared-card-projects">
              <span
                v-for="pid in entry.projects"
                :key="pid"
                class="shared-project-chip"
              >
                {{ projectName(pid) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Network Graph ─── -->
    <section class="section" id="network">
      <div class="section-inner wide">
        <div class="section-label">The Map</div>
        <h2 class="section-title">Architecture network</h2>
        <p class="section-desc">
          Project nodes (large) connect to the technologies they use (small). Click any node to focus it — everything unrelated fades out. Filter by category to isolate parts of the stack.
        </p>

        <div class="graph-controls">
          <button
            v-for="cat in Object.keys(data?.categories || {})"
            :key="cat"
            :class="['graph-filter', { active: visibleCategories.has(cat) }]"
            :style="{ borderColor: data.categories[cat].color }"
            @click="toggleCategory(cat)"
          >
            <span
              class="graph-filter-dot"
              :style="{ background: data.categories[cat].color }"
            ></span>
            {{ data.categories[cat].label }}
          </button>
          <button class="graph-reset" @click="resetGraph">Reset View</button>
        </div>

        <div class="graph-wrap">
          <div ref="graphContainer" class="graph-canvas"></div>
          <div class="graph-legend">
            <div class="graph-legend-item">
              <span class="graph-legend-square legend-project"></span> Project
            </div>
            <div class="graph-legend-item">
              <span class="graph-legend-circle"></span> Technology
            </div>
          </div>
        </div>

        <!-- Selected node detail panel -->
        <div v-if="selectedNode" class="node-detail">
          <button class="node-detail-close" @click="clearSelection">×</button>
          <div class="node-detail-label">{{ selectedNode.kind === 'project' ? 'Project' : 'Technology' }}</div>
          <div class="node-detail-name">{{ selectedNode.name }}</div>
          <div v-if="selectedNode.kind === 'project'">
            <p class="node-detail-purpose">{{ selectedNode.project.purpose }}</p>
            <div class="node-detail-list-label">Tech stack ({{ flattenStack(selectedNode.project.stack).length }})</div>
            <div class="node-detail-list">
              <span
                v-for="tech in flattenStack(selectedNode.project.stack)"
                :key="tech"
                class="node-detail-pill"
              >
                {{ tech }}
              </span>
            </div>
          </div>
          <div v-else>
            <div class="node-detail-list-label">Used by {{ techToProjects.get(selectedNode.name)?.length || 0 }} project(s)</div>
            <div class="node-detail-list">
              <span
                v-for="pid in techToProjects.get(selectedNode.name) || []"
                :key="pid"
                class="node-detail-pill"
              >
                {{ projectName(pid) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Sankey-style flow ─── -->
    <section class="section section-alt">
      <div class="section-inner wide">
        <div class="section-label">Cross-Project Flow</div>
        <h2 class="section-title">Projects → technologies</h2>
        <p class="section-desc">
          A different angle on the same data: projects on the left, the top {{ flowTopN }} most-used technologies on the right, curves between them where there's a dependency. Hover or click any node to highlight just its connections.
        </p>

        <div class="flow-shell">
          <div ref="flowContainer" class="flow-canvas"></div>
        </div>
      </div>
    </section>

    <!-- ─── Stats Footer ─── -->
    <section class="section">
      <div class="section-inner wide">
        <div class="section-label">By the Numbers</div>
        <h2 class="section-title">Architecture at a glance</h2>

        <div class="numbers-grid">
          <div class="number-card">
            <div class="number-card-value">{{ data?.projects.length || 0 }}</div>
            <div class="number-card-label">Total Projects</div>
          </div>
          <div class="number-card">
            <div class="number-card-value">{{ uniqueTechCount }}</div>
            <div class="number-card-label">Unique Technologies</div>
          </div>
          <div class="number-card">
            <div class="number-card-value">{{ uniqueLanguages.length }}</div>
            <div class="number-card-label">Programming Languages</div>
          </div>
          <div class="number-card">
            <div class="number-card-value">{{ uniqueDatabases.length }}</div>
            <div class="number-card-label">Database Engines</div>
          </div>
          <div class="number-card">
            <div class="number-card-value">{{ uniqueAIProviders.length }}</div>
            <div class="number-card-label">AI Providers</div>
          </div>
          <div class="number-card">
            <div class="number-card-value">{{ runningCount }}</div>
            <div class="number-card-label">Currently Running</div>
          </div>
        </div>

        <div class="lang-breakdown">
          <h3 class="lang-breakdown-title">Languages</h3>
          <div class="lang-bars">
            <div
              v-for="lang in languageBreakdown"
              :key="lang.name"
              class="lang-bar-row"
            >
              <div class="lang-bar-name">{{ lang.name }}</div>
              <div class="lang-bar-track">
                <div
                  class="lang-bar-fill"
                  :style="{ width: (lang.count / langMax * 100) + '%' }"
                ></div>
              </div>
              <div class="lang-bar-count">{{ lang.count }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── How This Was Built ─── -->
    <section class="section section-alt">
      <div class="section-inner">
        <div class="section-label">Meta</div>
        <h2 class="section-title">How this page was built</h2>
        <p class="section-desc">
          Every line of this page was written by Claude Code in a single Discord-driven session.
          The user asked for an "enterprise architecture repository" with a network graph; Claude scanned every project on the Mac, generated the data, scaffolded the Vue app, wired up vis-network and a d3 flow chart, and exposed it via Tailscale Funnel.
        </p>

        <div class="vibe-stats">
          <div class="vibe-stat">
            <div class="vibe-stat-value">1</div>
            <div class="vibe-stat-label">Discord session</div>
          </div>
          <div class="vibe-stat">
            <div class="vibe-stat-value">~12</div>
            <div class="vibe-stat-label">Prompts to Claude</div>
          </div>
          <div class="vibe-stat">
            <div class="vibe-stat-value">{{ data?.projects.length || 0 }}</div>
            <div class="vibe-stat-label">Projects scanned</div>
          </div>
          <div class="vibe-stat">
            <div class="vibe-stat-value">~2k</div>
            <div class="vibe-stat-label">Lines of Vue / CSS</div>
          </div>
          <div class="vibe-stat">
            <div class="vibe-stat-value">Opus 4.6</div>
            <div class="vibe-stat-label">Model</div>
          </div>
          <div class="vibe-stat">
            <div class="vibe-stat-value">0</div>
            <div class="vibe-stat-label">Lines hand-written</div>
          </div>
        </div>

        <div class="meta-pipeline">
          <h3 class="meta-pipeline-title">How the data is collected</h3>
          <div class="meta-steps">
            <div class="meta-step">
              <div class="meta-step-num">1</div>
              <div class="meta-step-content">
                <h4 class="meta-step-title">Scan</h4>
                <p class="meta-step-desc">
                  <code>scripts/scan_projects.py</code> walks every included project directory and reads <code>package.json</code>, <code>requirements.txt</code>, <code>pyproject.toml</code>, and <code>docker-compose.yml</code>.
                  It detects languages (from manifest types + tsconfig presence), frontend frameworks, backend frameworks, databases, AI provider SDKs, build tools, and auth libraries.
                </p>
              </div>
            </div>
            <div class="meta-arrow">↓</div>
            <div class="meta-step">
              <div class="meta-step-num">2</div>
              <div class="meta-step-content">
                <h4 class="meta-step-title">Curate</h4>
                <p class="meta-step-desc">
                  Auto-detection misses cross-cutting infrastructure (Tailscale, WhatsApp Business API, Zep Cloud as a memory backend, Docker volumes), and it can't know <em>purpose</em>, <em>port assignments</em>, or current <em>status</em>. Those live in <code>data/tech_stack.json</code> as a hand-curated layer that's preserved across re-scans.
                </p>
              </div>
            </div>
            <div class="meta-arrow">↓</div>
            <div class="meta-step">
              <div class="meta-step-num">3</div>
              <div class="meta-step-content">
                <h4 class="meta-step-title">Render</h4>
                <p class="meta-step-desc">
                  The Vue page fetches <code>/tech_stack.json</code> on mount and computes everything else live: technology→project mappings, shared-tech rankings, network graph nodes/edges, sankey flow ranks, language breakdowns. No backend, no API — one JSON file is the entire source of truth.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="meta-stack-callout">
          <div class="meta-stack-title">Built with</div>
          <div class="meta-stack-tags">
            <span class="meta-stack-tag">Vue 3 (Composition API)</span>
            <span class="meta-stack-tag">Vite</span>
            <span class="meta-stack-tag">vis-network</span>
            <span class="meta-stack-tag">d3.js</span>
            <span class="meta-stack-tag">Space Grotesk + DM Sans</span>
            <span class="meta-stack-tag">Tailscale Funnel</span>
            <span class="meta-stack-tag">Claude Code (Opus 4.6)</span>
          </div>
        </div>
      </div>
    </section>


    <footer class="page-footer">
      <div class="footer-inner">
        <div class="footer-meta">Generated {{ data?.generated_at }} · Auto-detect + hand-curated · Refresh by re-running <code>python3 scripts/scan_projects.py</code></div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import * as d3 from 'd3'

const data = ref(null)
const graphContainer = ref(null)
const flowContainer = ref(null)
const selectedNode = ref(null)
const expandedTech = ref(null)
const expandedFromProject = ref(null)
const expandedProjects = ref(new Set())
const activeCategory = ref('All')
const visibleCategories = ref(new Set())
const flowTopN = 28
let network = null
let nodesDS = null
let edgesDS = null

// Hand-curated enterprise-architecture details for the most important tools.
// Anything not in here gets a generic auto-generated description.
const TECH_DETAILS = {
  'FastAPI': {
    role: 'Python Web Framework',
    vendor: 'Tiangolo (open source)',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Strategic standard for Python services',
    desc: 'Modern async Python web framework built on Starlette. Used as the standard backend for every project in this estate that needs a real API. Type-safe via Pydantic v2, automatic OpenAPI 3.1 documentation, async-first request handling. Selected over Flask for type safety, async DB support, and built-in OpenAPI generation.',
    specs: [
      { label: 'Language', value: 'Python 3.11+' },
      { label: 'ASGI Server', value: 'Uvicorn (uvloop)' },
      { label: 'Validation', value: 'Pydantic v2' },
      { label: 'OpenAPI', value: '3.1 (auto-generated)' },
      { label: 'Request mode', value: 'Async' },
      { label: 'Versions in estate', value: '0.115.x' },
    ],
    dependsOn: ['Python 3.11+', 'Uvicorn', 'Pydantic'],
    alternatives: ['Flask', 'Django REST', 'Litestar', 'Quart'],
    usedFor: ['REST APIs', 'Async DB queries', 'Auth + JWT', 'OpenAPI docs', 'File uploads', 'Background tasks'],
    docs: 'https://fastapi.tiangolo.com',
  },
  'Uvicorn': {
    role: 'ASGI Server',
    vendor: 'Encode (open source)',
    license: 'BSD-3-Clause',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Standard ASGI server for FastAPI services',
    desc: 'Production ASGI server based on uvloop and httptools. Always paired with FastAPI in this stack. Handles HTTP/1.1 + WebSocket, supports graceful reload in dev mode.',
    specs: [
      { label: 'Mode', value: 'standard (uvloop + httptools)' },
      { label: 'Protocol', value: 'HTTP/1.1, WebSocket' },
      { label: 'Workers', value: '1 (single-process per service)' },
    ],
    dependsOn: ['uvloop', 'httptools'],
    alternatives: ['Hypercorn', 'Daphne', 'Granian'],
    usedFor: ['Serving FastAPI apps', 'WebSocket connections'],
    docs: 'https://www.uvicorn.org',
  },
  'SQLAlchemy': {
    role: 'Python ORM',
    vendor: 'SQLAlchemy / Mike Bayer',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Strategic standard for Python data access',
    desc: 'Python\'s standard ORM. Used in async mode (asyncio extension) with asyncpg for non-blocking PostgreSQL. Paired with Alembic for schema migrations. Code uses the modern 2.0-style declarative mappings throughout.',
    specs: [
      { label: 'Version', value: '2.0+' },
      { label: 'Mode', value: 'Async (asyncio)' },
      { label: 'Driver', value: 'asyncpg' },
      { label: 'Migrations', value: 'Alembic' },
      { label: 'Style', value: '2.0 declarative' },
    ],
    dependsOn: ['asyncpg', 'Alembic'],
    alternatives: ['Tortoise ORM', 'SQLModel', 'Piccolo', 'raw asyncpg'],
    usedFor: ['Database models', 'Query building', 'Migrations', 'Connection pooling'],
    docs: 'https://www.sqlalchemy.org',
  },
  'Vue 3': {
    role: 'Frontend Framework',
    vendor: 'Vue.js (Evan You / OSS)',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Strategic standard for Vue-based UIs',
    desc: 'Reactive JavaScript framework. Default frontend choice across the estate. Composition API + <script setup>, single-file components, paired with Vite. Selected over React for smaller bundle, simpler reactivity model, and faster onboarding.',
    specs: [
      { label: 'Version', value: '3.5+' },
      { label: 'API style', value: 'Composition API + <script setup>' },
      { label: 'Router', value: 'vue-router 4' },
      { label: 'Build', value: 'Vite' },
      { label: 'TypeScript', value: 'Optional, used in caio-reports' },
    ],
    dependsOn: ['Vite', 'vue-router'],
    alternatives: ['React', 'Svelte', 'Solid'],
    usedFor: ['Reactive UIs', 'Component composition', 'Client routing', 'SFC styling'],
    docs: 'https://vuejs.org',
  },
  'React': {
    role: 'Frontend Framework',
    vendor: 'Meta (Facebook)',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used selectively for projects with React ecosystem libraries',
    desc: 'Used in projects that need the broader React ecosystem (HeroUI, Radix, Next.js). Versions 18 and 19. An internal AI Hub project uses React 19 + HeroUI for its design system.',
    specs: [
      { label: 'Versions in estate', value: '18, 19' },
      { label: 'Common with', value: 'Next.js, Vite' },
      { label: 'Server components', value: 'Yes (with Next.js)' },
    ],
    dependsOn: ['react-dom'],
    alternatives: ['Vue 3', 'Solid', 'Preact'],
    usedFor: ['Component-driven UIs', 'Server components (Next.js)', 'HeroUI integration'],
    docs: 'https://react.dev',
  },
  'React 19': {
    role: 'Frontend Framework',
    vendor: 'Meta',
    license: 'MIT',
    maturity: 'Recently released',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Adopted in newest projects (ai-hub, state-of-ai)',
    desc: 'React 19 — brings server components, async transitions, and the new use() hook. Adopted in ai-hub and state-of-ai for better SSR ergonomics.',
    specs: [
      { label: 'Version', value: '19' },
      { label: 'Server Components', value: 'Yes' },
    ],
    alternatives: ['React 18', 'Vue 3'],
    usedFor: ['Server components', 'Async UIs', 'Modern hooks'],
    docs: 'https://react.dev/blog',
  },
  'Next.js': {
    role: 'React Meta-Framework',
    vendor: 'Vercel',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free OSS / Vercel hosting paid',
    lockInRisk: 'High',
    adoptionStatus: 'Standard for full-stack React apps in this estate',
    desc: 'React framework with file-based routing, server components, and built-in API routes. Used for GenAI Recruit, ai-tracker, and state-of-ai. App Router only, no Pages Router. Lock-in is high due to Vercel-specific build conventions, but the apps run fine self-hosted.',
    specs: [
      { label: 'Versions', value: '14, 15, 16' },
      { label: 'Router', value: 'App Router' },
      { label: 'Bundlers', value: 'Webpack / Turbopack' },
    ],
    dependsOn: ['React', 'Node 20+'],
    alternatives: ['Remix', 'Astro', 'SvelteKit', 'TanStack Start'],
    usedFor: ['Full-stack React apps', 'SSR/SSG', 'API routes', 'i18n routing'],
    docs: 'https://nextjs.org',
  },
  'Next.js 14': {
    role: 'React Meta-Framework', vendor: 'Vercel', license: 'MIT', maturity: 'Mature', cost: 'Free / OSS', lockInRisk: 'High',
    desc: 'Next.js 14 with stable App Router. Used in ai-tracker.',
    specs: [{ label: 'Version', value: '14.2' }, { label: 'Router', value: 'App Router' }],
    usedFor: ['Full-stack React', 'Server actions'],
    docs: 'https://nextjs.org',
  },
  'Next.js 15': {
    role: 'React Meta-Framework', vendor: 'Vercel', license: 'MIT', maturity: 'Recent', cost: 'Free / OSS', lockInRisk: 'High',
    desc: 'Next.js 15 with stable Turbopack. Used in genai-recruit for fast HMR and builds.',
    specs: [{ label: 'Version', value: '15.5' }, { label: 'Bundler', value: 'Turbopack' }],
    usedFor: ['Full-stack React', 'Async request APIs'],
    docs: 'https://nextjs.org/blog/next-15',
  },
  'Next.js 16': {
    role: 'React Meta-Framework', vendor: 'Vercel', license: 'MIT', maturity: 'Bleeding edge', cost: 'Free / OSS', lockInRisk: 'High',
    desc: 'Next.js 16 — bleeding edge. Used in state-of-ai. Brings improved server actions and React 19 alignment.',
    specs: [{ label: 'Version', value: '16.2' }],
    usedFor: ['App Router', 'React 19 features'],
    docs: 'https://nextjs.org',
  },
  'PostgreSQL': {
    role: 'Relational Database',
    vendor: 'PostgreSQL Global Development Group',
    license: 'PostgreSQL License (BSD-like)',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Default datastore across the estate',
    desc: 'The default datastore. Every project that needs a real DB runs its own dedicated PostgreSQL container on a unique port (5432–5439) to avoid conflicts. The pgvector extension is used wherever embeddings are needed. Backups via pg_dump.',
    specs: [
      { label: 'Version', value: '16' },
      { label: 'Image', value: 'postgres:16-alpine / pgvector/pgvector:pg16' },
      { label: 'Drivers', value: 'asyncpg (Python), postgres (TS)' },
      { label: 'Backup', value: 'pg_dump --clean --if-exists' },
      { label: 'Hosting', value: 'Local Docker (per-project port)' },
    ],
    dependsOn: ['Docker'],
    alternatives: ['MySQL', 'CockroachDB', 'SQLite (embedded)', 'Supabase'],
    usedFor: ['Persistent storage', 'Relational queries', 'Vector search (pgvector)', 'Full-text search'],
    docs: 'https://www.postgresql.org/docs',
  },
  'pgvector': {
    role: 'Vector Search Extension',
    vendor: 'pgvector (Andrew Kane / OSS)',
    license: 'PostgreSQL License',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Standard for embedding storage',
    desc: 'PostgreSQL extension that adds a vector column type and similarity search operators. Powers the RAG / semantic search features in ai-hub, ai-radar, and alsheraa-phasing. Avoids the operational overhead of running a separate vector database.',
    specs: [
      { label: 'Extension version', value: '0.7+' },
      { label: 'Max dimensions', value: '16,000' },
      { label: 'Distance ops', value: 'Cosine, L2, inner product' },
      { label: 'Index types', value: 'IVFFlat, HNSW' },
      { label: 'Used dimensions', value: '768 (Gemini), 1536 (OpenAI)' },
    ],
    dependsOn: ['PostgreSQL'],
    alternatives: ['ChromaDB', 'Qdrant', 'Pinecone', 'Weaviate'],
    usedFor: ['Embedding storage', 'Semantic search', 'RAG retrieval', 'Similar item discovery'],
    docs: 'https://github.com/pgvector/pgvector',
  },
  'Redis': {
    role: 'In-Memory Store',
    vendor: 'Redis Ltd',
    license: 'RSALv2 / SSPLv1',
    maturity: 'Mature',
    cost: 'Free OSS / paid cloud',
    lockInRisk: 'Low',
    adoptionStatus: 'Used as Celery broker + cache where needed',
    desc: 'In-memory data store. Used as the Celery broker in ai-hub and as a general-purpose cache. Runs in Docker on port 6379. Note: Redis re-licensed in 2024 — long-term we may shift to Valkey (the OSS fork).',
    specs: [
      { label: 'Version', value: '7' },
      { label: 'Image', value: 'redis:7-alpine' },
      { label: 'Persistence', value: 'AOF + RDB' },
      { label: 'Memory limit', value: '128MB' },
    ],
    dependsOn: ['Docker'],
    alternatives: ['Valkey', 'KeyDB', 'Dragonfly', 'Memcached'],
    usedFor: ['Celery message broker', 'Caching', 'Rate limiting', 'Session storage'],
    docs: 'https://redis.io',
  },
  'SQLite': {
    role: 'Embedded Database',
    vendor: 'SQLite Consortium (D. R. Hipp)',
    license: 'Public Domain',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Used for single-user lightweight apps',
    desc: 'File-backed embedded database. Used by lighter projects that don\'t justify a full Postgres container — claude-dashboard, state-of-ai (via libSQL adapter). Zero ops overhead.',
    specs: [
      { label: 'Version', value: '3.x' },
      { label: 'Mode', value: 'File-backed, single-process' },
      { label: 'Adapter (TS)', value: '@libsql/client' },
    ],
    alternatives: ['DuckDB', 'PostgreSQL', 'libSQL'],
    usedFor: ['Local-only dashboards', 'Lightweight CRUD', 'Embedded analytics'],
    docs: 'https://www.sqlite.org',
  },
  'Vite': {
    role: 'Frontend Build Tool',
    vendor: 'Vue.js / Evan You',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Strategic standard for non-Next.js frontends',
    desc: 'The build tool for nearly every Vue / non-Next.js React project here. Native ESM dev server with instant HMR, Rollup-based production bundling, plugin pipeline. Selected over Webpack for dev speed.',
    specs: [
      { label: 'Versions in estate', value: '6 (most), 7, 8 (caio-reports)' },
      { label: 'HMR', value: 'Yes (instant)' },
      { label: 'Bundler', value: 'Rollup (production)' },
      { label: 'Dev server', value: 'Native ESM' },
    ],
    dependsOn: ['Node 20+'],
    alternatives: ['Webpack', 'Parcel', 'Turbopack', 'esbuild', 'Rspack'],
    usedFor: ['Dev server with HMR', 'Production bundling', 'Plugin pipeline'],
    docs: 'https://vitejs.dev',
  },
  'Docker': {
    role: 'Containerization',
    vendor: 'Docker Inc',
    license: 'Apache-2.0 (engine)',
    maturity: 'Mature',
    cost: 'Free Desktop personal use / paid Business',
    lockInRisk: 'Low',
    adoptionStatus: 'Standard for local infrastructure',
    desc: 'Almost every project ships a docker-compose.yml that brings up its database (and sometimes Redis or Celery workers). Tailscale exposes selected services to the internet. Zero K8s — single-node Docker Compose throughout.',
    specs: [
      { label: 'Compose version', value: '3.9 / latest spec' },
      { label: 'Networks', value: 'Per-project + shared (jarvis_default)' },
      { label: 'Volumes', value: 'Per-project named volumes' },
      { label: 'Engine', value: 'Docker Desktop on macOS' },
    ],
    alternatives: ['Podman', 'OrbStack', 'Colima', 'Lima'],
    usedFor: ['Database containers', 'Redis/Celery', 'Reproducible setup', 'Service isolation'],
    docs: 'https://docs.docker.com',
  },
  'Tailscale': {
    role: 'Mesh VPN + Funnel',
    vendor: 'Tailscale Inc',
    license: 'BSD-3 (client) / proprietary control plane',
    maturity: 'Mature',
    cost: 'Free for personal (up to 100 devices)',
    lockInRisk: 'Medium',
    adoptionStatus: 'Strategic standard for remote access + public exposure',
    desc: 'Hadi\'s Mac mini exposes services to the internet via Cloudflare Tunnel — leaderboard at leaderboard.hadismac.com. Also gives Hadi remote SSH access from any device on his tailnet without port-forwarding.',
    specs: [
      { label: 'Domain', value: 'leaderboard.hadismac.com' },
      { label: 'CDN', value: 'Cloudflare' },
      { label: 'Tailnet size', value: '< 10 devices' },
      { label: 'TLS', value: 'Auto (Let\'s Encrypt via Tailscale)' },
    ],
    dependsOn: ['WireGuard'],
    alternatives: ['ngrok', 'Cloudflare Tunnel', 'frp', 'self-hosted WireGuard'],
    usedFor: ['Internet exposure', 'TLS termination', 'No port-forwarding', 'Remote SSH'],
    docs: 'https://tailscale.com/kb',
  },
  'Tailscale Funnel': {
    role: 'Public HTTPS Proxy',
    vendor: 'Tailscale Inc',
    license: 'Proprietary (Tailscale-managed)',
    maturity: 'Generally Available',
    cost: 'Included in free tier',
    lockInRisk: 'Medium',
    adoptionStatus: 'Standard for sharing local services publicly',
    desc: 'A specific Tailscale feature that proxies a localhost port to a public HTTPS URL with a Tailscale-managed certificate. Used to make development services reachable from anywhere with no DNS, no port-forwarding, and no router config.',
    specs: [
      { label: 'Active funnels', value: ':443, :8443, :10000' },
      { label: 'Cert', value: 'Auto-rotated' },
      { label: 'Auth', value: 'Open (no auth at funnel layer)' },
    ],
    dependsOn: ['Tailscale'],
    alternatives: ['ngrok', 'Cloudflare Tunnel', 'localtunnel'],
    usedFor: ['Public HTTPS proxy', 'Sharing dev work', 'No DNS / no router config'],
    docs: 'https://tailscale.com/kb/1223/funnel',
  },
  'OpenAI': {
    role: 'AI Provider',
    vendor: 'OpenAI',
    license: 'Proprietary API',
    maturity: 'Mature',
    cost: 'Pay-per-token',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used for core LLM + embedding calls (mitigated by OpenRouter routing)',
    desc: 'OpenAI SDK used by ai-hub for chat completions and embeddings. Some calls are routed through OpenRouter as a unified gateway, which makes provider swap-out a single env var change.',
    specs: [
      { label: 'SDK', value: 'openai-python >= 1.60' },
      { label: 'Common models', value: 'gpt-4o, text-embedding-3-large' },
      { label: 'Embedding dim', value: '1536' },
    ],
    alternatives: ['Anthropic', 'Google Gemini', 'OpenRouter (routed)', 'Mistral'],
    usedFor: ['Chat completions', 'Embeddings', 'Function calling', 'Vision (gpt-4o)'],
    docs: 'https://platform.openai.com/docs',
  },
  'OpenRouter': {
    role: 'LLM Gateway',
    vendor: 'OpenRouter Inc',
    license: 'Proprietary',
    maturity: 'Production',
    cost: 'Pay-per-token (slight markup over upstream)',
    lockInRisk: 'Low',
    adoptionStatus: 'Used as unified provider abstraction',
    desc: 'Unified API gateway that routes calls to multiple model providers behind a single API key and an OpenAI-compatible interface. Used by ai-hub (chat) and openclaw (TheFel agent). Lets you swap models with a string change and gives consolidated cost tracking.',
    specs: [
      { label: 'Format', value: 'OpenAI-compatible' },
      { label: 'Common model', value: 'google/gemini-3-flash-preview' },
      { label: 'Models available', value: '300+' },
      { label: 'Streaming', value: 'SSE' },
    ],
    alternatives: ['LiteLLM (self-hosted)', 'Direct provider SDKs'],
    usedFor: ['Multi-model routing', 'Single API key', 'Cost tracking', 'Provider abstraction'],
    docs: 'https://openrouter.ai/docs',
  },
  'Anthropic Claude': {
    role: 'AI Provider',
    vendor: 'Anthropic',
    license: 'Proprietary API',
    maturity: 'Mature',
    cost: 'Pay-per-token',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used for high-quality reasoning + document tasks',
    desc: 'Anthropic\'s Claude API used by alsheraa-phasing (document understanding), caio-reports (narrative generation), and openclaw\'s reasoning chains. Claude Opus 4.6 + Sonnet 4.6 are the active models. Also the model behind Claude Code, which writes most of these projects.',
    specs: [
      { label: 'SDK', value: 'anthropic-python' },
      { label: 'Active models', value: 'Opus 4.6, Sonnet 4.6, Haiku 4.5' },
      { label: 'Context', value: '1M tokens (Opus 4.6 1M)' },
    ],
    alternatives: ['OpenAI', 'Google Gemini', 'OpenRouter (routed)'],
    usedFor: ['Document analysis', 'Report generation', 'Reasoning tasks', 'Code generation (via Claude Code)'],
    docs: 'https://docs.anthropic.com',
  },
  'Google Gemini': {
    role: 'AI Provider',
    vendor: 'Google',
    license: 'Proprietary API',
    maturity: 'Mature',
    cost: 'Pay-per-token (free tier exists)',
    lockInRisk: 'Medium',
    adoptionStatus: 'Workhorse for classification + embeddings',
    desc: 'Google\'s Gemini family. Used as the classification + embedding workhorse in ai-radar (Gemini 3 Flash for enrichment, Gemini Embedding 2 for vectors), and as the primary model for openclaw via OpenRouter. Selected for its price-performance on bulk classification.',
    specs: [
      { label: 'SDKs', value: 'google-genai, google-generativeai' },
      { label: 'Active models', value: 'Gemini 3 Flash, Gemini text-embedding-004' },
      { label: 'Embedding dim', value: '768' },
      { label: 'Free tier', value: 'Yes' },
    ],
    alternatives: ['OpenAI', 'Anthropic', 'Voyage AI (embeddings)'],
    usedFor: ['Classification', 'Embeddings', 'Agent reasoning', 'Bulk enrichment'],
    docs: 'https://ai.google.dev/docs',
  },
  'Voyage AI': {
    role: 'Embedding Provider',
    vendor: 'Voyage AI',
    license: 'Proprietary API',
    maturity: 'Recent',
    cost: 'Pay-per-token',
    lockInRisk: 'Low',
    adoptionStatus: 'Used where embedding quality matters most',
    desc: 'High-quality embedding models. Used in alsheraa-phasing for semantic search across documents and integrations. Often outperforms OpenAI text-embedding-3 on retrieval benchmarks at lower cost.',
    specs: [
      { label: 'SDK', value: 'voyageai-python' },
      { label: 'Common model', value: 'voyage-3' },
    ],
    alternatives: ['OpenAI embeddings', 'Gemini Embedding 2', 'Cohere'],
    usedFor: ['Document embeddings', 'Semantic search', 'High-quality retrieval'],
    docs: 'https://docs.voyageai.com',
  },
  'Zep Cloud': {
    role: 'Memory Backend',
    vendor: 'Zep',
    license: 'Proprietary cloud / OSS engine',
    maturity: 'Production',
    cost: 'Free tier / paid cloud',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used for agent memory in OpenClaw',
    desc: 'Long-term memory store for AI agents. Used by openclaw (TheFel) to remember conversations across sessions and by swarmcast for agent state. Provides fact extraction, summarization, and graph memory.',
    specs: [
      { label: 'Tier', value: 'Cloud (Zep Cloud)' },
      { label: 'Features', value: 'Sessions, facts, summaries' },
    ],
    alternatives: ['Mem0', 'Letta', 'Self-hosted Postgres + embeddings'],
    usedFor: ['Agent memory', 'Session history', 'Fact extraction', 'Conversation summarization'],
    docs: 'https://docs.getzep.com',
  },
  'JWT': {
    role: 'Auth Token Standard',
    vendor: 'IETF (RFC 7519)',
    license: 'Standard',
    maturity: 'Mature',
    cost: 'Free standard',
    lockInRisk: 'Low',
    adoptionStatus: 'Strategic standard for stateless auth',
    desc: 'JSON Web Tokens — the default auth scheme across the FastAPI + Next.js projects. Stored in HTTP-only cookies, validated server-side. Symmetric HS256 signing throughout (no asymmetric keys yet).',
    specs: [
      { label: 'Standard', value: 'RFC 7519' },
      { label: 'Algorithm', value: 'HS256' },
      { label: 'Lib (Python)', value: 'python-jose' },
      { label: 'Lib (TS)', value: 'jsonwebtoken' },
      { label: 'Storage', value: 'HTTP-only cookies' },
    ],
    alternatives: ['Session cookies', 'Paseto', 'Branca'],
    usedFor: ['Stateless auth', 'API session tokens', 'Service-to-service auth'],
    docs: 'https://datatracker.ietf.org/doc/html/rfc7519',
  },
  'next-auth': {
    role: 'Auth Library',
    vendor: 'Next-Auth.js / Auth.js',
    license: 'ISC',
    maturity: 'Mature (v5 in beta)',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Standard auth for Next.js apps',
    desc: 'Next.js auth library. Used in genai-recruit for user sessions, OAuth providers, and credentials auth. Currently on the v5 beta which renames to Auth.js.',
    specs: [
      { label: 'Version', value: '5.0 beta' },
      { label: 'Strategy', value: 'JWT sessions' },
      { label: 'Providers', value: 'Credentials + OAuth' },
    ],
    dependsOn: ['Next.js'],
    alternatives: ['Lucia', 'Clerk', 'Better Auth', 'Supabase Auth'],
    usedFor: ['Session management', 'OAuth providers', 'Credentials auth'],
    docs: 'https://authjs.dev',
  },
  'Drizzle ORM': {
    role: 'TypeScript ORM',
    vendor: 'Drizzle Team',
    license: 'Apache-2.0',
    maturity: 'Production',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Used in genai-recruit instead of Prisma',
    desc: 'TypeScript-first ORM with SQL-like syntax. Used in genai-recruit instead of Prisma for sharper type inference, smaller runtime, and edge-runtime compatibility.',
    specs: [
      { label: 'Driver', value: 'postgres (npm)' },
      { label: 'Migrations', value: 'drizzle-kit' },
      { label: 'Edge-compatible', value: 'Yes' },
    ],
    dependsOn: ['postgres (driver)'],
    alternatives: ['Prisma', 'Kysely', 'TypeORM', 'raw SQL'],
    usedFor: ['Type-safe queries', 'Schema migrations', 'Edge-runtime DB access'],
    docs: 'https://orm.drizzle.team',
  },
  'Prisma': {
    role: 'TypeScript ORM',
    vendor: 'Prisma Data Inc',
    license: 'Apache-2.0',
    maturity: 'Mature',
    cost: 'Free OSS / paid cloud (Pulse, Accelerate)',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used in state-of-ai with libSQL adapter',
    desc: 'TypeScript ORM with a schema-first approach. Used in state-of-ai with the libSQL adapter for SQLite-on-the-edge compatibility.',
    specs: [
      { label: 'Adapter', value: '@prisma/adapter-libsql' },
      { label: 'Schema', value: 'schema.prisma' },
      { label: 'Migrations', value: 'prisma migrate' },
    ],
    alternatives: ['Drizzle ORM', 'Kysely', 'TypeORM'],
    usedFor: ['Schema modeling', 'Type-safe queries', 'Migrations'],
    docs: 'https://www.prisma.io/docs',
  },
  'Celery': {
    role: 'Distributed Task Queue',
    vendor: 'Celery (open source)',
    license: 'BSD-3-Clause',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Medium',
    adoptionStatus: 'Used in ai-hub for background processing',
    desc: 'Distributed task queue. Used in ai-hub for background jobs (file processing, embedding generation, report generation). Backed by Redis as the broker. Single worker pool with prefork concurrency.',
    specs: [
      { label: 'Broker', value: 'Redis' },
      { label: 'Worker model', value: 'prefork' },
      { label: 'Concurrency', value: 'CPU count' },
      { label: 'Result backend', value: 'Redis' },
    ],
    dependsOn: ['Redis'],
    alternatives: ['ARQ', 'Dramatiq', 'RQ', 'Taskiq'],
    usedFor: ['Async jobs', 'Scheduled tasks', 'File processing', 'Embedding generation'],
    docs: 'https://docs.celeryq.dev',
  },
  'APScheduler': {
    role: 'Python Scheduler',
    vendor: 'AP Scheduler (OSS)',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Standard for in-process Python scheduling',
    desc: 'In-process scheduler for FastAPI apps. Powers ai-radar\'s data collection cron (every 30min / 4hr / 12hr) and ai-tracker\'s sync jobs. Simpler than Celery beat for single-process schedules.',
    specs: [
      { label: 'Triggers', value: 'cron, interval, date' },
      { label: 'Mode', value: 'In-process' },
    ],
    alternatives: ['Celery beat', 'Cron + endpoint', 'Temporal'],
    usedFor: ['Periodic jobs', 'Data collection cron', 'Sync workflows'],
    docs: 'https://apscheduler.readthedocs.io',
  },
  'd3': {
    role: 'Visualization Library',
    vendor: 'D3.js (Mike Bostock / OSS)',
    license: 'ISC',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Strategic standard for custom visualizations',
    desc: 'Low-level data visualization library. Used in ai-radar for the radar chart, in alsheraa-phasing for the integration map and hub flow, and in this very page for the cross-project flow chart. Selected for the flexibility of building bespoke charts SVG-by-SVG.',
    specs: [
      { label: 'Version', value: '7.9' },
      { label: 'Renderer', value: 'SVG' },
      { label: 'Modules used', value: 'd3-selection, d3-shape, d3-scale' },
    ],
    alternatives: ['Plotly', 'Chart.js', 'ECharts', 'Observable Plot'],
    usedFor: ['Radar charts', 'Hub-flow diagrams', 'Sankey-style flows', 'Custom SVG viz'],
    docs: 'https://d3js.org',
  },
  'vis-network': {
    role: 'Network Graph Library',
    vendor: 'vis.js community',
    license: 'Apache-2.0 / MIT',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Used for force-directed graphs',
    desc: 'Higher-level graph library on top of canvas with built-in physics (Barnes-Hut). Used in alsheraa-phasing\'s integration map and in this page\'s architecture network. Faster than d3-force for graphs with 100+ nodes.',
    specs: [
      { label: 'Renderer', value: 'Canvas' },
      { label: 'Physics', value: 'Barnes-Hut N-body' },
      { label: 'Version', value: '9.x' },
    ],
    alternatives: ['Cytoscape.js', 'd3-force', 'react-force-graph', 'sigma.js'],
    usedFor: ['Force-directed graphs', 'Interactive networks', 'Cluster visualization'],
    docs: 'https://visjs.github.io/vis-network',
  },
  'Tailwind CSS': {
    role: 'Utility CSS Framework',
    vendor: 'Tailwind Labs',
    license: 'MIT',
    maturity: 'Mature',
    cost: 'Free OSS / Tailwind UI paid components',
    lockInRisk: 'Low',
    adoptionStatus: 'Used in Next.js / React projects',
    desc: 'Utility-first CSS. Used in ai-hub, ai-tracker, state-of-ai. Other (Vue) projects use the hand-rolled "AI Radar" design system instead. Tailwind v4 uses native CSS, no PostCSS plugin needed.',
    specs: [
      { label: 'Versions in estate', value: '3, 4' },
      { label: 'Engine (v4)', value: 'Native CSS, no PostCSS' },
    ],
    alternatives: ['UnoCSS', 'Vanilla Extract', 'Hand-rolled design tokens'],
    usedFor: ['Component styling', 'Responsive layouts', 'Design tokens'],
    docs: 'https://tailwindcss.com/docs',
  },
  'Flask': {
    role: 'Python Web Framework',
    vendor: 'Pallets Projects',
    license: 'BSD-3-Clause',
    maturity: 'Mature',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Inherited from upstream MiroFish, not preferred for new code',
    desc: 'Lighter Python web framework — used by SwarmCast (the upstream MiroFish project ships with Flask, not FastAPI). For new projects, FastAPI is preferred for type safety and async.',
    specs: [
      { label: 'Extension', value: 'flask-cors' },
      { label: 'Mode', value: 'Sync (WSGI)' },
    ],
    alternatives: ['FastAPI', 'Litestar', 'Quart'],
    usedFor: ['Simple REST endpoints', 'Inherited upstream code'],
    docs: 'https://flask.palletsprojects.com',
  },
  'ChromaDB': {
    role: 'Vector Database',
    vendor: 'Chroma',
    license: 'Apache-2.0',
    maturity: 'Production',
    cost: 'Free OSS / paid cloud',
    lockInRisk: 'Low',
    adoptionStatus: 'Used by SwarmCast (upstream choice)',
    desc: 'Standalone vector database. Used by SwarmCast for embedding storage instead of pgvector — inherited from the upstream MiroFish project. For new projects, pgvector is preferred to avoid running a separate database service.',
    specs: [
      { label: 'Mode', value: 'Embedded or server' },
      { label: 'Backing store', value: 'DuckDB / Parquet' },
    ],
    alternatives: ['pgvector', 'Qdrant', 'Weaviate', 'LanceDB'],
    usedFor: ['Embedding storage', 'RAG retrieval'],
    docs: 'https://docs.trychroma.com',
  },
  'Bun': {
    role: 'JavaScript Runtime + Toolchain',
    vendor: 'Oven',
    license: 'MIT',
    maturity: 'Production',
    cost: 'Free / OSS',
    lockInRisk: 'Low',
    adoptionStatus: 'Used in genai-recruit for fast scripts',
    desc: 'JavaScript runtime, package manager, and bundler. Used in genai-recruit for the seed scripts and as a faster alternative to npm install. The actual app still runs on Node + Next.js.',
    specs: [
      { label: 'Used for', value: 'Scripts (bun run scripts/seed.ts)' },
      { label: 'App runtime', value: 'Still Node 20+' },
    ],
    alternatives: ['Node + tsx', 'Deno', 'pnpm'],
    usedFor: ['Running TS scripts', 'Faster installs'],
    docs: 'https://bun.sh',
  },
}

onMounted(async () => {
  const resp = await fetch('/tech_stack.json')
  data.value = await resp.json()
  visibleCategories.value = new Set(Object.keys(data.value.categories))
  await nextTick()
  buildGraph()
  buildFlow()
})

watch(visibleCategories, () => {
  if (data.value) buildGraph()
}, { deep: true })

const projectCategories = computed(() => {
  if (!data.value) return ['All']
  const cats = new Set(['All'])
  data.value.projects.forEach(p => cats.add(p.category))
  return [...cats]
})

const filteredProjects = computed(() => {
  if (!data.value) return []
  if (activeCategory.value === 'All') return data.value.projects
  return data.value.projects.filter(p => p.category === activeCategory.value)
})

function projectsInCategory(cat) {
  if (!data.value) return []
  if (cat === 'All') return data.value.projects
  return data.value.projects.filter(p => p.category === cat)
}

function nonEmptyStack(stack) {
  const out = {}
  for (const [k, v] of Object.entries(stack)) {
    if (v && v.length) out[k] = v
  }
  return out
}

function flattenStack(stack) {
  return Object.values(stack).flat()
}

const uniqueTechCount = computed(() => {
  if (!data.value) return 0
  const set = new Set()
  for (const p of data.value.projects) {
    for (const tech of flattenStack(p.stack)) set.add(tech)
  }
  return set.size
})

const uniqueLanguages = computed(() => {
  if (!data.value) return []
  const set = new Set()
  for (const p of data.value.projects) {
    for (const l of p.stack.language || []) set.add(l)
  }
  return [...set]
})

const uniqueDatabases = computed(() => {
  if (!data.value) return []
  const set = new Set()
  for (const p of data.value.projects) {
    for (const d of p.stack.database || []) set.add(d)
  }
  return [...set]
})

const uniqueAIProviders = computed(() => {
  if (!data.value) return []
  const set = new Set()
  for (const p of data.value.projects) {
    for (const a of p.stack.ai_provider || []) set.add(a)
  }
  return [...set]
})

const runningCount = computed(() => {
  if (!data.value) return 0
  return data.value.projects.filter(p => p.status === 'running').length
})

const techToProjects = computed(() => {
  const m = new Map()
  if (!data.value) return m
  for (const p of data.value.projects) {
    for (const tech of flattenStack(p.stack)) {
      if (!m.has(tech)) m.set(tech, [])
      m.get(tech).push(p.id)
    }
  }
  return m
})

const techToCategory = computed(() => {
  const m = new Map()
  if (!data.value) return m
  for (const p of data.value.projects) {
    for (const [cat, items] of Object.entries(p.stack)) {
      for (const item of items) {
        if (!m.has(item)) m.set(item, cat)
      }
    }
  }
  return m
})

const topSharedTech = computed(() => {
  if (!data.value) return []
  const list = []
  for (const [name, projects] of techToProjects.value.entries()) {
    if (projects.length < 2) continue
    const cat = techToCategory.value.get(name)
    list.push({
      name,
      projects,
      color: data.value.categories[cat]?.color || '#999',
    })
  }
  list.sort((a, b) => b.projects.length - a.projects.length)
  return list.slice(0, 24)
})

const expandedTechDetail = computed(() => {
  if (!expandedTech.value || !data.value) return null
  const name = expandedTech.value
  const cat = techToCategory.value.get(name)
  const catLabel = data.value.categories[cat]?.label || cat || 'Technology'
  const projects = techToProjects.value.get(name) || []
  const curated = TECH_DETAILS[name]
  if (curated) {
    return { name, ...curated, projects }
  }
  // Auto-generated fallback
  return {
    name,
    role: catLabel,
    desc: `${name} is a ${catLabel.toLowerCase()} used in this stack. It appears in ${projects.length} project${projects.length === 1 ? '' : 's'}.`,
    specs: [],
    usedFor: [],
    projects,
  }
})

const languageBreakdown = computed(() => {
  if (!data.value) return []
  const counts = {}
  for (const p of data.value.projects) {
    for (const l of p.stack.language || []) {
      counts[l] = (counts[l] || 0) + 1
    }
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})

const langMax = computed(() => Math.max(1, ...languageBreakdown.value.map(l => l.count)))

function projectName(id) {
  return data.value?.projects.find(p => p.id === id)?.name || id
}

function toggleCategory(cat) {
  const next = new Set(visibleCategories.value)
  if (next.has(cat)) next.delete(cat)
  else next.add(cat)
  visibleCategories.value = next
}

function resetGraph() {
  visibleCategories.value = new Set(Object.keys(data.value.categories))
  clearSelection()
  if (network) network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
}

function clearSelection() {
  selectedNode.value = null
  if (network) {
    network.unselectAll()
    resetGraphHighlight()
  }
}

function toggleTechDetail(name, projectId = null) {
  if (expandedTech.value === name && expandedFromProject.value === projectId) {
    expandedTech.value = null
    expandedFromProject.value = null
  } else {
    expandedTech.value = name
    expandedFromProject.value = projectId
  }
}

function toggleProject(id) {
  const next = new Set(expandedProjects.value)
  if (next.has(id)) {
    next.delete(id)
    // If the open tech detail belonged to this card, close it too
    if (expandedFromProject.value === id) {
      expandedTech.value = null
      expandedFromProject.value = null
    }
  } else {
    next.add(id)
  }
  expandedProjects.value = next
}

function expandAllProjects() {
  if (!data.value) return
  expandedProjects.value = new Set(data.value.projects.map(p => p.id))
}

function collapseAllProjects() {
  expandedProjects.value = new Set()
  expandedTech.value = null
  expandedFromProject.value = null
}

function scrollToTechDetail() {
  nextTick(() => {
    const el = document.querySelector('.tech-detail')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function buildGraph() {
  if (!data.value || !graphContainer.value) return

  const nodes = []
  const edges = []
  const seenTech = new Set()

  for (const proj of data.value.projects) {
    nodes.push({
      id: `proj::${proj.id}`,
      label: proj.name,
      shape: 'box',
      color: {
        background: '#1a1917',
        border: '#14532d',
        highlight: { background: '#14532d', border: '#86efac' },
      },
      font: { color: '#faf9f7', face: 'Space Grotesk', size: 16, bold: '700' },
      borderWidth: 2,
      margin: 12,
      shapeProperties: { borderRadius: 6 },
      _kind: 'project',
      _project: proj,
      _baseColor: { background: '#1a1917', border: '#14532d' },
      _baseFont: { color: '#faf9f7' },
    })

    for (const [cat, items] of Object.entries(proj.stack)) {
      if (!visibleCategories.value.has(cat)) continue
      const color = data.value.categories[cat]?.color || '#999'
      for (const tech of items) {
        const techId = `tech::${tech}`
        if (!seenTech.has(techId)) {
          seenTech.add(techId)
          nodes.push({
            id: techId,
            label: tech,
            shape: 'dot',
            size: 12,
            color: {
              background: color,
              border: color,
              highlight: { background: color, border: '#1a1917' },
            },
            font: { color: '#23221f', face: 'DM Sans', size: 12 },
            _kind: 'tech',
            _tech: tech,
            _category: cat,
            _baseColor: { background: color, border: color },
            _baseFont: { color: '#23221f' },
          })
        }
        edges.push({
          from: `proj::${proj.id}`,
          to: techId,
          color: { color: color + '66', highlight: color },
          width: 1.5,
          _baseColor: color + '66',
        })
      }
    }
  }

  const techConnCount = {}
  for (const e of edges) techConnCount[e.to] = (techConnCount[e.to] || 0) + 1
  for (const n of nodes) {
    if (n._kind === 'tech') {
      const c = techConnCount[n.id] || 1
      n.size = 8 + c * 3
      n.font.size = c >= 3 ? 14 : 11
    }
  }

  if (network) {
    network.destroy()
    network = null
  }

  nodesDS = new DataSet(nodes)
  edgesDS = new DataSet(edges)

  network = new Network(graphContainer.value, { nodes: nodesDS, edges: edgesDS }, {
    nodes: {
      borderWidth: 1,
      scaling: { min: 20, max: 60 },
    },
    edges: {
      smooth: { type: 'continuous', roundness: 0.2 },
      selectionWidth: 2,
    },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -8000,
        centralGravity: 0.25,
        springLength: 140,
        springConstant: 0.04,
        damping: 0.6,
      },
      stabilization: { iterations: 250 },
    },
    interaction: {
      hover: true,
      dragNodes: true,
      tooltipDelay: 200,
    },
  })

  network.on('selectNode', (params) => {
    const nodeId = params.nodes[0]
    const node = nodesDS.get(nodeId)
    if (!node) return
    if (node._kind === 'project') {
      selectedNode.value = { kind: 'project', name: node._project.name, project: node._project }
    } else {
      selectedNode.value = { kind: 'tech', name: node._tech }
    }
    applyGraphHighlight(nodeId)
  })

  network.on('deselectNode', () => {
    // user clicked the canvas (not a node)
    clearSelection()
  })

  network.on('click', (params) => {
    if (params.nodes.length === 0) {
      clearSelection()
    }
  })
}

function applyGraphHighlight(centerId) {
  if (!network || !nodesDS || !edgesDS) return
  const connectedNodes = new Set([centerId, ...network.getConnectedNodes(centerId)])
  const connectedEdges = new Set(network.getConnectedEdges(centerId))

  nodesDS.update(nodesDS.get().map(n => {
    const isHighlighted = connectedNodes.has(n.id)
    if (n._kind === 'project') {
      return {
        id: n.id,
        color: isHighlighted
          ? { background: '#1a1917', border: '#14532d' }
          : { background: '#e5e4e1', border: '#d1cfc9' },
        font: { color: isHighlighted ? '#faf9f7' : '#a8a69f', face: 'Space Grotesk', size: 16, bold: '700' },
      }
    } else {
      const baseBg = n._baseColor.background
      return {
        id: n.id,
        color: isHighlighted
          ? { background: baseBg, border: baseBg }
          : { background: '#e5e4e1', border: '#d1cfc9' },
        font: { color: isHighlighted ? '#23221f' : '#a8a69f', face: 'DM Sans', size: n.font.size },
      }
    }
  }))

  edgesDS.update(edgesDS.get().map(e => {
    const isHighlighted = connectedEdges.has(e.id)
    return {
      id: e.id,
      color: { color: isHighlighted ? e._baseColor.replace('66', 'cc') : '#e5e4e133' },
      width: isHighlighted ? 2.5 : 0.8,
    }
  }))
}

function resetGraphHighlight() {
  if (!network || !nodesDS || !edgesDS) return
  nodesDS.update(nodesDS.get().map(n => {
    if (n._kind === 'project') {
      return {
        id: n.id,
        color: { background: '#1a1917', border: '#14532d' },
        font: { color: '#faf9f7', face: 'Space Grotesk', size: 16, bold: '700' },
      }
    } else {
      const baseBg = n._baseColor.background
      return {
        id: n.id,
        color: { background: baseBg, border: baseBg },
        font: { color: '#23221f', face: 'DM Sans', size: n.font.size },
      }
    }
  }))
  edgesDS.update(edgesDS.get().map(e => ({
    id: e.id,
    color: { color: e._baseColor },
    width: 1.5,
  })))
}

// ─── Sankey-style cross-project flow ───
function buildFlow() {
  if (!data.value || !flowContainer.value) return

  d3.select(flowContainer.value).selectAll('*').remove()

  // Top-N most-used technologies
  const techRanked = []
  for (const [name, projects] of techToProjects.value.entries()) {
    techRanked.push({ name, count: projects.length, projects })
  }
  techRanked.sort((a, b) => b.count - a.count)
  const topTech = techRanked.slice(0, flowTopN)
  const topTechSet = new Set(topTech.map(t => t.name))

  const projects = data.value.projects.map(p => {
    const techsUsed = flattenStack(p.stack).filter(t => topTechSet.has(t))
    return { id: p.id, label: p.name, count: techsUsed.length, techsUsed }
  }).filter(p => p.count > 0)

  // Layout
  const PROJ_R_MAX = 22
  const PROJ_R_MIN = 12
  const TECH_R = 6
  const ROW_H = 30
  const PADDING = 50

  // Wrap labels
  function wrap(text, max) {
    if (!text || text.length <= max) return [text]
    const idx = text.lastIndexOf(' ', max)
    if (idx > 0) return [text.slice(0, idx), text.slice(idx + 1)]
    return [text]
  }

  const projLabelLines = {}
  for (const p of projects) projLabelLines[p.id] = wrap(p.label, 22)
  const techLabelLines = {}
  for (const t of topTech) techLabelLines[t.name] = wrap(t.name, 26)

  const longestProj = Math.max(...Object.values(projLabelLines).map(ls => Math.max(...ls.map(l => l.length))))
  const longestTech = Math.max(...Object.values(techLabelLines).map(ls => Math.max(...ls.map(l => l.length))))
  const CHAR_W = 6.5
  const projLabelSpace = longestProj * CHAR_W + 30
  const techLabelSpace = longestTech * CHAR_W + 30

  const PROJ_X = projLabelSpace + PROJ_R_MAX + 16
  const TECH_X = PROJ_X + 360

  const maxConn = Math.max(...projects.map(p => p.count), 1)
  function projRadius(c) {
    return PROJ_R_MIN + (PROJ_R_MAX - PROJ_R_MIN) * (c / maxConn)
  }

  // Group tech nodes by category for visual ordering
  topTech.forEach(t => {
    t._category = techToCategory.value.get(t.name)
  })
  topTech.sort((a, b) => {
    const ca = a._category || ''
    const cb = b._category || ''
    if (ca !== cb) return ca.localeCompare(cb)
    return b.count - a.count
  })

  const techColH = topTech.length * ROW_H
  const projColH = projects.length * (PROJ_R_MAX * 2 + 14)
  const totalH = Math.max(techColH, projColH) + PADDING * 2

  const techPos = {}
  topTech.forEach((t, i) => {
    techPos[t.name] = {
      x: TECH_X,
      y: PADDING + i * ROW_H + ROW_H / 2,
      label: t.name,
      count: t.count,
      category: t._category,
    }
  })

  const projPos = {}
  const projSpan = totalH - PADDING * 2
  projects.forEach((p, i) => {
    const t = projects.length === 1 ? 0.5 : i / (projects.length - 1)
    projPos[p.id] = {
      x: PROJ_X,
      y: PADDING + t * projSpan,
      label: p.label,
      count: p.count,
      r: projRadius(p.count),
    }
  })

  const totalW = TECH_X + techLabelSpace + 20

  const svg = d3.select(flowContainer.value)
    .append('svg')
    .attr('viewBox', `0 0 ${totalW} ${totalH}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .style('width', '100%')
    .style('min-width', `${Math.min(totalW, 1100)}px`)
    .style('display', 'block')

  function curve(x1, y1, x2, y2) {
    const cpDx = (x2 - x1) * 0.5
    return `M${x1},${y1} C${x1 + cpDx},${y1} ${x2 - cpDx},${y2} ${x2},${y2}`
  }

  const HIGHLIGHT = '#14532d'
  const projNodeEls = {}
  const techNodeEls = {}
  const linkRecords = []

  // Lines (drawn first)
  const linesG = svg.append('g').attr('class', 'lines')
  for (const p of projects) {
    const pp = projPos[p.id]
    for (const tech of p.techsUsed) {
      const tp = techPos[tech]
      if (!tp) continue
      const cat = techToCategory.value.get(tech)
      const baseColor = data.value.categories[cat]?.color || '#85837c'
      const path = linesG.append('path')
        .attr('d', curve(pp.x + pp.r, pp.y, tp.x - TECH_R, tp.y))
        .attr('stroke', baseColor)
        .attr('stroke-width', 1.2)
        .attr('stroke-opacity', 0.32)
        .attr('fill', 'none')
      linkRecords.push({ projId: p.id, tech, el: path.node(), color: baseColor })
    }
  }

  // Project nodes (left)
  const projsG = svg.append('g').attr('class', 'projects')
  for (const p of projects) {
    const pp = projPos[p.id]
    const g = projsG.append('g')
      .attr('transform', `translate(${pp.x}, ${pp.y})`)
      .attr('class', 'flow-project-node')
      .style('cursor', 'pointer')
      .on('mouseover', () => { if (!flowPinned) highlightProject(p.id) })
      .on('mouseout', () => { if (!flowPinned) clearFlowHighlight() })
      .on('click', (event) => {
        event.stopPropagation()
        if (flowPinned && flowPinned.type === 'proj' && flowPinned.id === p.id) unpinFlow()
        else pinProject(p.id)
      })
    projNodeEls[p.id] = g.node()

    g.append('circle')
      .attr('r', pp.r)
      .attr('fill', HIGHLIGHT)
      .attr('stroke', HIGHLIGHT)
      .attr('stroke-width', 2)
      .attr('fill-opacity', 0.92)

    const lines = projLabelLines[p.id]
    const lineH = 14
    const totalLines = lines.length + 1
    let cy = -((totalLines - 1) / 2) * lineH

    for (const line of lines) {
      g.append('text')
        .attr('x', -pp.r - 10)
        .attr('y', cy)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .style('font-family', "'Space Grotesk', sans-serif")
        .style('font-size', '13px')
        .style('font-weight', '700')
        .style('fill', '#23221f')
        .text(line)
      cy += lineH
    }

    g.append('text')
      .attr('x', -pp.r - 10)
      .attr('y', cy)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .style('font-family', "'JetBrains Mono', monospace")
      .style('font-size', '10px')
      .style('fill', '#85837c')
      .text(`${pp.count} tech`)
  }

  // Tech nodes (right)
  const techsG = svg.append('g').attr('class', 'techs')
  for (const t of topTech) {
    const tp = techPos[t.name]
    const cat = techToCategory.value.get(t.name)
    const color = data.value.categories[cat]?.color || '#85837c'
    const g = techsG.append('g')
      .attr('transform', `translate(${tp.x}, ${tp.y})`)
      .attr('class', 'flow-tech-node')
      .style('cursor', 'pointer')
      .on('mouseover', () => { if (!flowPinned) highlightTech(t.name) })
      .on('mouseout', () => { if (!flowPinned) clearFlowHighlight() })
      .on('click', (event) => {
        event.stopPropagation()
        if (flowPinned && flowPinned.type === 'tech' && flowPinned.id === t.name) unpinFlow()
        else pinTech(t.name)
      })
    techNodeEls[t.name] = g.node()

    g.append('circle')
      .attr('r', TECH_R)
      .attr('fill', color)
      .attr('stroke', '#faf9f7')
      .attr('stroke-width', 1.5)

    const lines = techLabelLines[t.name]
    const lineH = 13
    let cy = -((lines.length - 1) / 2) * lineH
    for (const line of lines) {
      g.append('text')
        .attr('x', TECH_R + 8)
        .attr('y', cy)
        .attr('dominant-baseline', 'middle')
        .style('font-family', "'DM Sans', sans-serif")
        .style('font-size', '12px')
        .style('font-weight', '500')
        .style('fill', '#23221f')
        .text(line)
      cy += lineH
    }
    g.append('text')
      .attr('x', TECH_R + 8)
      .attr('y', cy + 2)
      .attr('dominant-baseline', 'middle')
      .style('font-family', "'JetBrains Mono', monospace")
      .style('font-size', '9px')
      .style('fill', '#85837c')
      .text(`× ${t.count}`)
  }

  let flowPinned = null

  function highlightProject(pid) {
    const targetTechs = new Set()
    for (const link of linkRecords) {
      const on = link.projId === pid
      link.el.style.strokeOpacity = on ? 0.95 : 0.05
      link.el.style.strokeWidth = on ? 2.2 : '1'
      if (on) targetTechs.add(link.tech)
    }
    for (const id in projNodeEls) projNodeEls[id].style.opacity = id === pid ? 1 : 0.18
    for (const t in techNodeEls) techNodeEls[t].style.opacity = targetTechs.has(t) ? 1 : 0.18
  }

  function highlightTech(name) {
    const sourceProjs = new Set()
    for (const link of linkRecords) {
      const on = link.tech === name
      link.el.style.strokeOpacity = on ? 0.95 : 0.05
      link.el.style.strokeWidth = on ? 2.2 : '1'
      if (on) sourceProjs.add(link.projId)
    }
    for (const id in projNodeEls) projNodeEls[id].style.opacity = sourceProjs.has(id) ? 1 : 0.18
    for (const t in techNodeEls) techNodeEls[t].style.opacity = t === name ? 1 : 0.18
  }

  function clearFlowHighlight() {
    for (const link of linkRecords) {
      link.el.style.strokeOpacity = 0.32
      link.el.style.strokeWidth = '1'
    }
    for (const id in projNodeEls) projNodeEls[id].style.opacity = 1
    for (const t in techNodeEls) techNodeEls[t].style.opacity = 1
  }

  function pinProject(pid) {
    flowPinned = { type: 'proj', id: pid }
    highlightProject(pid)
  }
  function pinTech(name) {
    flowPinned = { type: 'tech', id: name }
    highlightTech(name)
  }
  function unpinFlow() {
    flowPinned = null
    clearFlowHighlight()
  }
  svg.on('click', () => {
    if (flowPinned) unpinFlow()
  })
}
</script>

<style scoped>
.arch-page {
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
}

/* ── Hero ── */
.hero {
  padding: 110px 24px 80px;
  text-align: center;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(20, 83, 45, 0.07) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(98, 70, 234, 0.05) 0%, transparent 50%),
    var(--bg-primary);
}
.hero-inner { max-width: 760px; margin: 0 auto; }
.hero-badge {
  display: inline-block;
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--accent-500);
  background: var(--accent-50);
  padding: 6px 16px;
  border-radius: var(--radius-full);
  margin-bottom: 24px;
}
.hero-title {
  font-family: var(--font-display);
  font-size: 60px;
  font-weight: 700;
  letter-spacing: -1.5px;
  line-height: 1.05;
  color: var(--text-primary);
  margin-bottom: 22px;
}
.hero-sub {
  font-size: 20px;
  line-height: 1.6;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto 48px;
}
.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 36px;
  margin-bottom: 48px;
  flex-wrap: wrap;
}
.hero-stat { text-align: center; }
.hero-stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 38px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.15;
}
.hero-stat-label { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.hero-stat-divider { width: 1px; height: 42px; background: var(--border-light); }
.hero-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: var(--accent-500);
  padding: 14px 32px;
  border-radius: var(--radius-full);
  text-decoration: none;
  transition: all var(--transition-fast);
}
.hero-cta:hover {
  background: var(--accent-600);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(13, 115, 119, 0.2);
  text-decoration: none;
}

/* ── Sections ── */
.section { padding: 84px 24px; }
.section-alt { background: var(--bg-secondary); }
.section-inner { max-width: 920px; margin: 0 auto; }
.section-inner.wide { max-width: 1180px; }
.section-label {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--accent-500);
  margin-bottom: 12px;
}
.section-title {
  font-family: var(--font-display);
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  margin-bottom: 16px;
  line-height: 1.2;
}
.section-desc {
  font-size: 17px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin-bottom: 40px;
  max-width: 720px;
}

/* ── Category tabs ── */
.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}
.category-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--border-light);
  background: var(--bg-primary);
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.category-tab:hover { border-color: var(--accent-500); color: var(--text-primary); }
.category-tab.active { background: var(--accent-500); border-color: var(--accent-500); color: white; }
.category-tab-count {
  background: rgba(255,255,255,0.2);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-size: 11px;
}
.category-tab:not(.active) .category-tab-count { background: var(--bg-tertiary); color: var(--text-tertiary); }

.expand-all-controls {
  display: flex;
  gap: 6px;
  margin-left: auto;
}
.expand-all-btn {
  padding: 7px 14px;
  border: 1px solid var(--border-default);
  background: var(--bg-primary);
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.expand-all-btn:hover {
  border-color: var(--accent-500);
  color: var(--accent-500);
}

/* ── BIG Project Cards ── */
.project-grid-big {
  display: grid;
  grid-template-columns: 1fr;
  gap: 28px;
}
.project-card-big {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  overflow: hidden;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.project-card-big:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-md);
}
.project-card-big.is-running {
  border-left: 3px solid var(--color-success);
}
.project-card-big.is-collapsed .big-card-header-btn {
  border-bottom: none;
}

/* Clickable header button (always visible) */
.big-card-header-btn {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  width: 100%;
  padding: 24px 32px;
  background: none;
  border: none;
  border-bottom: 1px solid var(--border-light);
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: background var(--transition-fast);
}
.big-card-header-btn:hover {
  background: var(--bg-secondary);
}
.card-chevron {
  flex-shrink: 0;
  margin-top: 6px;
  color: var(--text-tertiary);
  transition: transform 200ms var(--ease-out), color var(--transition-fast);
}
.card-chevron.open {
  transform: rotate(90deg);
  color: var(--accent-500);
}
.big-card-header-content { flex: 1; min-width: 0; }
.big-card-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.big-card-meta-item {
  font-family: var(--font-display);
  font-weight: 600;
}
.big-card-meta-sep { color: var(--border-default); }
.big-card-path-inline {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}

.big-card-body {
  padding: 28px 32px 32px;
}
.card-expand-enter-active { transition: all 350ms var(--ease-out); }
.card-expand-leave-active { transition: all 250ms var(--ease-out); }
.card-expand-enter-from,
.card-expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.card-expand-enter-to,
.card-expand-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.big-card-header { margin-bottom: 24px; }
.big-card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 6px;
}
.big-card-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.big-card-status {
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 11px;
  border-radius: var(--radius-full);
  white-space: nowrap;
}
.status-running { background: rgba(45,157,120,0.12); color: var(--color-success); }
.status-stopped { background: var(--bg-tertiary); color: var(--text-tertiary); }
.status-partial { background: rgba(212,148,10,0.12); color: var(--color-warning); }
.status-in-development { background: rgba(59,130,246,0.12); color: var(--color-info); }

.big-card-path {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 14px;
}
.big-card-purpose {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 16px;
}
.big-card-ports {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.port-pill {
  font-family: var(--font-mono);
  font-size: 10px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: 3px 9px;
  border-radius: var(--radius-sm);
}

/* ── Stack groups inside big card ── */
.big-stack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 22px 24px;
  padding-top: 22px;
  border-top: 1px dashed var(--border-light);
}
.big-stack-group {}
.big-stack-heading {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid;
}
.big-stack-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.big-stack-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: none;
  cursor: pointer;
  text-align: left;
  font-family: var(--font-sans);
  font-weight: 500;
  width: 100%;
  transition: all 150ms var(--ease-out);
}
.big-stack-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-light);
}
.big-stack-item.active {
  background: var(--accent-50);
  color: var(--accent-600);
  border-color: var(--accent-200);
}
.big-stack-item-text { flex: 1; }
.big-stack-chevron {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 150ms, transform 200ms var(--ease-out);
}
.big-stack-item:hover .big-stack-chevron { opacity: 0.4; }
.big-stack-item.active .big-stack-chevron { opacity: 1; transform: rotate(180deg); }

/* ── Tech Detail Panel (global, shared) ── */
.tech-detail {
  margin-top: 32px;
  padding: 32px;
  border: 1px solid var(--accent-200);
  border-radius: var(--radius-lg);
  background: var(--accent-50);
  position: relative;
}
.tech-detail-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.tech-detail-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.tech-detail-role {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-500);
  background: var(--accent-100);
  padding: 3px 12px;
  border-radius: var(--radius-full);
}
.tech-detail-close {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  font-size: 22px;
  line-height: 1;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 150ms;
}
.tech-detail-close:hover { background: var(--bg-hover); color: var(--text-primary); }
.tech-detail-desc {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.65;
  margin-bottom: 22px;
  max-width: 860px;
}

/* Enterprise field grid */
.tech-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 18px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}
.tech-field { display: flex; flex-direction: column; gap: 4px; }
.tech-field-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-muted);
}
.tech-field-value {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.maturity-pill, .risk-pill {
  display: inline-block;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius-full);
}
.maturity-mature { background: rgba(45,157,120,0.12); color: var(--color-success); }
.maturity-production { background: rgba(45,157,120,0.12); color: var(--color-success); }
.maturity-generally-available { background: rgba(45,157,120,0.12); color: var(--color-success); }
.maturity-recent { background: rgba(59,130,246,0.12); color: var(--color-info); }
.maturity-recently-released { background: rgba(59,130,246,0.12); color: var(--color-info); }
.maturity-bleeding-edge { background: rgba(212,148,10,0.12); color: var(--color-warning); }

.risk-low { background: rgba(45,157,120,0.12); color: var(--color-success); }
.risk-medium { background: rgba(212,148,10,0.12); color: var(--color-warning); }
.risk-high { background: rgba(214,69,69,0.12); color: var(--color-error); }

.tech-detail-specs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
.tech-spec { display: flex; flex-direction: column; gap: 3px; }
.tech-spec-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}
.tech-spec-value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.tech-detail-usage { margin-bottom: 16px; }
.tech-detail-usage:last-child { margin-bottom: 0; }
.tech-usage-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 8px;
}
.tech-usage-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tech-usage-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 11px;
  border-radius: var(--radius-full);
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
}
.tech-usage-tag-purpose {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-color: transparent;
}

.tech-detail-footer {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--accent-200);
}
.tech-detail-link {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-500);
  text-decoration: none;
}
.tech-detail-link:hover {
  color: var(--accent-600);
  text-decoration: underline;
}

.tech-expand-enter-active { transition: all 300ms var(--ease-out); }
.tech-expand-leave-active { transition: all 200ms var(--ease-out); }
.tech-expand-enter-from,
.tech-expand-leave-to { opacity: 0; transform: translateY(-8px); }
.tech-expand-enter-to,
.tech-expand-leave-from { opacity: 1; transform: translateY(0); }

/* ── Shared tech grid ── */
.shared-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.shared-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  padding: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.shared-card:hover { border-color: var(--border-default); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.shared-card-top { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.shared-card-dot { width: 10px; height: 10px; border-radius: 50%; }
.shared-card-name {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}
.shared-card-count {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.shared-card-projects { display: flex; flex-wrap: wrap; gap: 4px; }
.shared-project-chip {
  font-size: 10px;
  font-family: var(--font-mono);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  padding: 2px 7px;
  border-radius: var(--radius-sm);
}

/* ── Network graph ── */
.graph-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  align-items: center;
}
.graph-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid var(--border-light);
  background: var(--bg-primary);
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  opacity: 0.45;
  transition: all var(--transition-fast);
}
.graph-filter.active { opacity: 1; }
.graph-filter:hover { color: var(--text-primary); }
.graph-filter-dot { width: 8px; height: 8px; border-radius: 50%; }
.graph-reset {
  padding: 7px 14px;
  border: 1px solid var(--border-default);
  background: var(--bg-primary);
  border-radius: var(--radius-full);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-left: auto;
}
.graph-reset:hover { border-color: var(--accent-500); color: var(--accent-500); }
.graph-wrap {
  position: relative;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  height: 640px;
  overflow: hidden;
}
.graph-canvas { width: 100%; height: 100%; }
.graph-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  gap: 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: var(--font-display);
  font-weight: 600;
}
.graph-legend-item { display: flex; align-items: center; gap: 6px; }
.graph-legend-square {
  width: 14px;
  height: 12px;
  background: #1a1917;
  border: 2px solid var(--accent-500);
  border-radius: 3px;
}
.graph-legend-circle { width: 12px; height: 12px; border-radius: 50%; background: var(--accent-500); }

.node-detail {
  margin-top: 20px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  padding: 24px;
  position: relative;
}
.node-detail-close {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 20px;
  line-height: 1;
}
.node-detail-close:hover { background: var(--bg-active); color: var(--text-primary); }
.node-detail-label {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--accent-500);
  margin-bottom: 6px;
}
.node-detail-name {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.node-detail-purpose { font-size: 14px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 16px; }
.node-detail-list-label {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}
.node-detail-list { display: flex; flex-wrap: wrap; gap: 6px; }
.node-detail-pill {
  font-size: 12px;
  font-family: var(--font-display);
  background: var(--bg-secondary);
  color: var(--text-primary);
  padding: 4px 11px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-light);
}

/* ── Flow chart ── */
.flow-shell {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  padding: 24px;
  overflow-x: auto;
}
.flow-canvas { width: 100%; min-height: 700px; }

/* ── Numbers grid ── */
.numbers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.number-card {
  padding: 24px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  text-align: center;
}
.number-card-value {
  font-family: var(--font-display);
  font-size: 42px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.05;
  letter-spacing: -1px;
}
.number-card-label { font-size: 12px; color: var(--text-tertiary); margin-top: 8px; }

/* ── Language breakdown ── */
.lang-breakdown { margin-top: 32px; }
.lang-breakdown-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}
.lang-bars { display: flex; flex-direction: column; gap: 10px; }
.lang-bar-row {
  display: grid;
  grid-template-columns: 140px 1fr 50px;
  gap: 16px;
  align-items: center;
}
.lang-bar-name {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.lang-bar-track {
  background: var(--bg-tertiary);
  height: 14px;
  border-radius: var(--radius-full);
  overflow: hidden;
}
.lang-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-500), var(--accent-200));
  border-radius: var(--radius-full);
}
.lang-bar-count {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: right;
}

/* ── Vibe stats / meta ── */
.vibe-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.vibe-stat {
  padding: 22px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  text-align: center;
}
.vibe-stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
  letter-spacing: -0.5px;
}
.vibe-stat-label { font-size: 11px; color: var(--text-tertiary); margin-top: 6px; }

.meta-pipeline {
  margin-bottom: 40px;
}
.meta-pipeline-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-tertiary);
  margin-bottom: 20px;
}
.meta-steps { display: flex; flex-direction: column; gap: 12px; }
.meta-step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 22px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
}
.meta-step-num {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--accent-500);
  color: white;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.meta-step-content { flex: 1; }
.meta-step-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.meta-step-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.65;
}
.meta-step-desc code {
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-mono);
}
.meta-arrow {
  text-align: center;
  font-size: 24px;
  color: var(--accent-500);
}

.meta-stack-callout {
  padding: 24px;
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-lg);
  text-align: center;
}
.meta-stack-title {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-tertiary);
  margin-bottom: 14px;
}
.meta-stack-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.meta-stack-tag {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-light);
}

/* ── Footer ── */
.page-footer {
  padding: 32px 24px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-secondary);
}
.footer-inner { max-width: 1180px; margin: 0 auto; text-align: center; }
.footer-meta { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
.footer-meta code {
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .hero { padding: 70px 20px 60px; }
  .hero-title { font-size: 42px; }
  .hero-sub { font-size: 17px; }
  .section { padding: 60px 20px; }
  .section-title { font-size: 30px; }
  .big-stack-grid { grid-template-columns: 1fr; }
  .graph-wrap { height: 480px; }
  .lang-bar-row { grid-template-columns: 100px 1fr 40px; }
}
@media (max-width: 640px) {
  .hero-title { font-size: 32px; }
  .hero-stat-divider { display: none; }
  .hero-stats { gap: 18px; }
  .numbers-grid { grid-template-columns: repeat(2, 1fr); }
  .vibe-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
