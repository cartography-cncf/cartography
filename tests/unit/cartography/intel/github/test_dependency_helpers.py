"""
Unit tests for GitHub dependency helper functions used for Package ontology integration.
"""

from cartography.intel.github.repos import _extract_exact_version
from cartography.intel.github.repos import _make_dependency_purl


class TestExtractExactVersion:
    def test_plain_version(self):
        assert _extract_exact_version("18.2.0") == "18.2.0"

    def test_single_equals_prefix(self):
        assert _extract_exact_version("= 4.2.0") == "4.2.0"

    def test_double_equals_prefix(self):
        assert _extract_exact_version("== 4.2.0") == "4.2.0"

    def test_double_equals_no_space(self):
        assert _extract_exact_version("==1.0.0") == "1.0.0"

    def test_range_with_caret(self):
        assert _extract_exact_version("^4.17.21") is None

    def test_range_with_tilde(self):
        assert _extract_exact_version("~1.2.3") is None

    def test_range_with_greater_than(self):
        assert _extract_exact_version(">= 1.0") is None

    def test_range_with_less_than(self):
        assert _extract_exact_version("< 2.0") is None

    def test_range_with_comma(self):
        assert _extract_exact_version(">= 1.0, < 2.0") is None

    def test_wildcard(self):
        assert _extract_exact_version("1.*.*") is None

    def test_not_equal(self):
        assert _extract_exact_version("!= 1.0") is None

    def test_empty_string(self):
        assert _extract_exact_version("") is None

    def test_none(self):
        assert _extract_exact_version(None) is None

    def test_whitespace_only(self):
        assert _extract_exact_version("   ") is None


class TestMakeDependencyPurl:
    def test_simple_npm_package(self):
        result = _make_dependency_purl("react", "18.2.0", "npm", "NPM")
        assert result == "pkg:npm/react@18.2.0"

    def test_simple_pypi_package(self):
        result = _make_dependency_purl("Django", "4.2.0", "pypi", "PIP")
        assert result == "pkg:pypi/Django@4.2.0"

    def test_maven_namespace(self):
        result = _make_dependency_purl(
            "org.springframework:spring-core",
            "5.3.21",
            "maven",
            "MAVEN",
        )
        assert result == "pkg:maven/org.springframework/spring-core@5.3.21"

    def test_npm_scoped_package(self):
        result = _make_dependency_purl("@types/node", "18.0.0", "npm", "NPM")
        assert result == "pkg:npm/types/node@18.0.0"

    def test_simple_gem_package(self):
        result = _make_dependency_purl("rails", "7.0.0", "gem", "RUBYGEMS")
        assert result == "pkg:gem/rails@7.0.0"

    def test_golang_package(self):
        result = _make_dependency_purl(
            "github.com/gin-gonic/gin", "1.9.0", "golang", "GO"
        )
        assert result == "pkg:golang/github.com/gin-gonic/gin@1.9.0"
