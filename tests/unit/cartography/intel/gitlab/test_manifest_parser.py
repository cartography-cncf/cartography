"""Unit tests for GitLab manifest file parser."""

from cartography.intel.gitlab.manifest_parser import parse_gemfile
from cartography.intel.gitlab.manifest_parser import parse_go_mod
from cartography.intel.gitlab.manifest_parser import parse_package_json
from cartography.intel.gitlab.manifest_parser import parse_pipfile
from cartography.intel.gitlab.manifest_parser import parse_requirements_txt


class TestParseRequirementsTxt:
    def test_pinned_versions(self):
        content = "requests==2.31.0\nFlask==3.0.0\n"
        result = parse_requirements_txt(content)
        assert result["requests"] == "==2.31.0"
        assert result["flask"] == "==3.0.0"

    def test_version_ranges(self):
        content = "Django>=4.2,<5.0\ncelery>=5.0\n"
        result = parse_requirements_txt(content)
        assert result["django"] == ">=4.2,<5.0"
        assert result["celery"] == ">=5.0"

    def test_compatible_release(self):
        content = "requests~=2.31.0\n"
        result = parse_requirements_txt(content)
        assert result["requests"] == "~=2.31.0"

    def test_skips_comments_and_blanks(self):
        content = "# comment\n\nrequests==2.31.0\n  # indented comment\n"
        result = parse_requirements_txt(content)
        assert len(result) == 1
        assert result["requests"] == "==2.31.0"

    def test_skips_flags(self):
        content = "-r base.txt\n-e .\nrequests==2.31.0\n--index-url https://example.com\n"
        result = parse_requirements_txt(content)
        assert len(result) == 1

    def test_strips_inline_comments(self):
        content = "requests==2.31.0 # HTTP library\n"
        result = parse_requirements_txt(content)
        assert result["requests"] == "==2.31.0"

    def test_strips_environment_markers(self):
        content = 'requests==2.31.0; python_version >= "3.8"\n'
        result = parse_requirements_txt(content)
        assert result["requests"] == "==2.31.0"

    def test_no_version_spec_skipped(self):
        content = "requests\nFlask==3.0.0\n"
        result = parse_requirements_txt(content)
        # "requests" has no version spec, should be skipped
        assert "requests" not in result
        assert result["flask"] == "==3.0.0"

    def test_canonicalizes_python_names(self):
        content = "PyYAML==6.0\njaraco.context>=4.0\nmy_package==1.0\n"
        result = parse_requirements_txt(content)
        assert result["pyyaml"] == "==6.0"
        assert result["jaraco-context"] == ">=4.0"
        assert result["my-package"] == "==1.0"


class TestParsePipfile:
    def test_packages_section(self):
        content = """
[packages]
requests = ">=2.31.0"
Flask = "==3.0.0"

[dev-packages]
pytest = ">=7.0"
"""
        result = parse_pipfile(content)
        assert result["requests"] == ">=2.31.0"
        assert result["flask"] == "==3.0.0"
        assert result["pytest"] == ">=7.0"

    def test_skips_wildcard(self):
        content = """
[packages]
requests = "*"
Flask = "==3.0.0"
"""
        result = parse_pipfile(content)
        assert "requests" not in result
        assert result["flask"] == "==3.0.0"

    def test_ignores_other_sections(self):
        content = """
[requires]
python_version = "3.11"

[packages]
requests = ">=2.31.0"
"""
        result = parse_pipfile(content)
        assert len(result) == 1


class TestParsePackageJson:
    def test_dependencies_and_dev(self):
        content = """{
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "~4.17.0"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}"""
        result = parse_package_json(content)
        assert result["express"] == "^4.18.0"
        assert result["lodash"] == "~4.17.0"
        assert result["jest"] == "^29.0.0"

    def test_invalid_json(self):
        result = parse_package_json("not json")
        assert result == {}


class TestParseGoMod:
    def test_require_block(self):
        content = """module example.com/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/stretchr/testify v1.8.4 // indirect
)
"""
        result = parse_go_mod(content)
        assert result["github.com/gin-gonic/gin"] == "v1.9.1"
        assert result["github.com/stretchr/testify"] == "v1.8.4"

    def test_single_line_require(self):
        content = """module example.com/myproject

require github.com/gin-gonic/gin v1.9.1
"""
        result = parse_go_mod(content)
        assert result["github.com/gin-gonic/gin"] == "v1.9.1"


class TestParseGemfile:
    def test_gem_with_version(self):
        content = """source 'https://rubygems.org'

gem 'rails', '~> 7.0'
gem 'puma', '>= 5.0'
gem 'sqlite3'
"""
        result = parse_gemfile(content)
        assert result["rails"] == "~> 7.0"
        assert result["puma"] == ">= 5.0"
        # sqlite3 has no version, not included
        assert "sqlite3" not in result
