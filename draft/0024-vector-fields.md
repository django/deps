---
DEP: 0021
Author: Frank Wiles
Implementation Team: TBD
Shepherd: Frank Wiles
Status: Draft
Type: Feature
Created: 2026-09-27
---
# DEP 0021: Vector fields and similarity search

## Abstract

This DEP proposes a shared Django ORM API to store vectors and calculate
distances on supported database backends:

- `VectorField` stores dense or sparse vectors.
- `VectorDistance` calculates numeric distances.
- `VectorIndex` declares vector indexes.

Applications use shared Python values, including `SparseVector`, and enums.
Backends control database-specific storage, queries, and indexes.
Supported operations have the same meaning, but backend capabilities can differ.
The API uses Django's validation, migrations, and serialization.

Ordinary distance queries remain exact. Applications must explicitly request
approximate search; its query API is not yet defined. This proposal excludes
embedding generation and model-provider integrations.

## Motivation

Applications store numeric embeddings to find documents with related meanings,
similar images, or related products. A native vector column lets queries combine
ordinary filters with distance calculations on records in a relational database.
Applications need not copy candidate vectors into Python or synchronize a
separate vector service.

The missing feature is ORM support for an existing database type, not an
embedding model or an AI workflow. JSON or binary fields can store vectors.
They do not provide declared dimensions, native binding, distance expressions,
or vector index management. Raw SQL supports these operations, but applications
must manage conversion and migrations.

## Specification

### Scope and public API

This draft specifies field storage, exact distance expressions, and vector index
declarations. The approximate-search query API is not yet defined. Index support
for faster ORM searches requires this API. Otherwise, the initial release would
include only storage and exact distances.

The proposed public imports are:

```python
from django.db.models import (
    SparseVector,
    VectorDimension,
    VectorDistanceType,
    VectorField,
    VectorIndex,
    VectorIndexType,
    VectorStorageFormat,
    VectorStorageType,
)
from django.db.models.functions import VectorDistance
```

`VectorField`, `VectorDimension`, the enums, and `SparseVector` are defined in
`django.db.models.fields.vector` and re-exported from `django.db.models`.
Backends import these shared definitions, not each other's constants or driver
types. `VectorDistance` is exported from `django.db.models.functions`.

API imports, model declarations, and migration serialization must not require a
database driver or vector extension. NumPy is not required.

Each backend implements the capabilities it supports:

- Dense `FLOAT32`, `FLOAT64`, `INT8`, and packed `BINARY` vectors.
- Sparse `FLOAT32`, `FLOAT64`, and `INT8` vectors.
- Explicit distance calculations, including numeric threshold filtering.
- Migration-managed hierarchical navigable small world (HNSW) and inverted file
  (IVF) vector indexes where supported.

**Out of scope:** Embedding generation, vector arithmetic and aggregation,
automatic normalization, hybrid full-text search, reranking, and cross-database
fallback storage.

See [Backend integration](#backend-integration-and-unsupported-environments)
for target databases, capability checks, and unsupported-operation behavior.
Other backends can implement the API.

### VectorField

```python
VectorField(
    dimensions=6,
    storage_format=VectorStorageFormat.FLOAT32,
    storage_type=VectorStorageType.DENSE,
    **options,
)
```

`options` are standard model field options with the restrictions below.
The additional arguments are:

| Argument | Meaning |
| --- | --- |
| `dimensions` | Required. A positive integer number of dimensions, or the `VectorDimension.ANY` sentinel for variable-dimensional dense storage. There is no default; omitting `dimensions` raises `TypeError`. Booleans, `None`, and strings such as `"*"` or `"ANY"` are not valid dimensions. |
| `storage_format` | One of `FLOAT32`, `FLOAT64`, `INT8`, or `BINARY` from `VectorStorageFormat`. The default is `FLOAT32`. |
| `storage_type` | `VectorStorageType.DENSE` or `VectorStorageType.SPARSE`. The default is `DENSE`. |

Enum string values match their member names, are stable, and must support
migration serialization. The API accepts enum members, not arbitrary SQL strings.
Neither storage argument accepts `None`. The initial API excludes flexible
scalar formats and mixed dense/sparse columns. Only `dimensions` accepts `VectorDimension.ANY`.

`VectorDimension.ANY` is a public singleton sentinel on `VectorDimension`, not a SQL
string or vector value. It lets a column store vectors with different dimensions.

`VectorField(dimensions=3)` maps to Oracle's `VECTOR(3, FLOAT32, DENSE)` or pgvector's
`vector(3)`. `VectorField(dimensions=VectorDimension.ANY)` maps to
Oracle's `VECTOR(*, FLOAT32, DENSE)` or pgvector's `vector` without a dimension
modifier, as described in the [pgvector documentation][pgvector-variable].
These mappings use the default dense `FLOAT32` storage; other formats require
separate backend capability checks.

```python
from django.db import models


class VariableProduct(models.Model):
    embedding = models.VectorField(dimensions=models.VectorDimension.ANY)


VariableProduct.objects.create(embedding=[0.1, 0.2, 0.3])
VariableProduct.objects.create(embedding=[0.1, 0.2])
```

Each value must have a nonzero dimension. Distance operands must have equal
actual dimensions, even with `VectorDimension.ANY`.

Field declarations have these restrictions:

- Sparse fields require a positive integer `dimensions`; `VectorDimension.ANY` is not supported.
- Sparse `BINARY` storage is not supported.
- Binary dimensions count bits and, when specified, must be a multiple of eight.

Empty vectors are not treated as `NULL` or zero vectors.
`empty_strings_allowed` is false.

The initial implementation rejects `primary_key=True`, `unique=True`, and
`db_index=True`. Declare vector indexes in `Meta.indexes`, not as B-tree indexes.
Vector columns cannot be foreign-key targets. Unsupported vector constraints
and ordinary indexes on vector columns must produce system check errors.
They must not produce a different schema.

### Python values and validation

Vector shape and format checks also run during database preparation, including
bulk writes.

#### Dense values

For dense storage, assignments and query literals accept a Python list or an
`array.array`. Database reads return an `array.array` with the type code below:

| Storage format | Type code | Value representation |
| --- | --- | --- |
| `FLOAT32` | `f` | Finite 32-bit floating-point components. |
| `FLOAT64` | `d` | Finite 64-bit floating-point components. |
| `INT8` | `b` | Integers from -128 to 127. |
| `BINARY` | `B` | Packed bytes, each from 0 to 255. |

Dense floating-point lists can contain integers or floats, but not booleans.
Integer and binary formats reject fractional values without truncation.
Validation rejects non-finite values and overflow in the destination format.
Floating-point values are rounded to the declared precision, as documented.

An array must have the field's type code. Validation rejects other type codes
without reinterpretation. A fixed-dimensional numeric vector must contain `dimensions`
components. A binary vector must contain `dimensions / 8` bytes. For example, `[180, 150, 100]` represents a 24-dimensional
binary vector, not a three-dimensional vector. Variable-dimensional dense
vectors still must be nonempty and respect the database's maximum dimensions.

#### Sparse values

Sparse values require the common `SparseVector` class.

Its dimension must match the field. Indices must be zero-based integers,
strictly increasing, unique, and less than `dimensions`. Their count must equal the
value count. Explicit zero entries are not permitted. An all-zero sparse vector has empty
indices and values, subject to the backend capability tests below.
There is no automatic sorting, duplicate merging, or conversion between dense
and sparse storage.

Example:

```python
from django.db.models import SparseVector

query = SparseVector(dimensions=30, indices=[3, 10, 12], values=[2.5, 2.5, 1.0])
```

`SparseVector(dimensions, indices, values)` follows these validation rules and exposes
these three attributes. The constructor accepts a list or correctly typed array
for `values`. The field, not the constructor, validates and converts the storage
format. Both `to_python()` and database reads return a common `SparseVector`,
not a driver class. Its `indices` is a tuple of integers; its `values` is an
`array.array` with the field's type code. Backends perform driver conversion
and keep zero-based indices in Python.

Sparse values cannot use tuples because they could be confused with dense
sequences. NumPy users must convert data to lists or supported arrays.

### Distance expressions

```python
VectorDistance(lhs, rhs, distance=VectorDistanceType.EUCLIDEAN)
```

`VectorDistance` accepts vector-valued expressions and literals (lists, arrays,
or `SparseVector` instances). Literals are wrapped in
`Value` expressions using the other operand's resolved `VectorField`. If neither
operand provides that type, callers must supply explicitly typed `Value`
expressions; otherwise resolution raises `FieldError`.

Operands must have matching dimensions, scalar formats, and storage types.
Expression resolution or literal preparation rejects known incompatibilities.
For properties known only at execution, including variable dimensions, Django
wraps database errors in its database exceptions. The API prohibits mixed
dense/sparse comparisons, even if a database permits implicit conversion.

The output field is `FloatField`. Non-null results are Python floats.
If either operand is SQL `NULL`, the result is `None`.
Null ordering uses Django's standard expression ordering API.

`VectorDistanceType` provides:

| Member | Meaning |
| --- | --- |
| `EUCLIDEAN` | Euclidean (L2) distance. |
| `EUCLIDEAN_SQUARED` | Squared Euclidean distance. |
| `COSINE` | One minus cosine similarity. |
| `DOT` | **Negated** dot product, not positive inner product. |
| `MANHATTAN` | Sum of absolute component differences (L1). |
| `HAMMING` | Number of differing bit positions in binary vectors. |
| `JACCARD` | Jaccard distance on binary vectors. |

Metric support depends on database versions, extensions, and operand formats.
`HAMMING` and `JACCARD` require binary vectors. 

Django does not normalize vectors or supply fallback results for undefined
distances, such as cosine distance involving a zero vector. Each backend's
behavior must be documented and tested. 

`EUCLIDEAN` is the default. Django always specifies the SQL metric, without
using database defaults or index-based inference. Values other than
`VectorDistanceType` members raise `TypeError`.

Example:

```python
from django.db import models
from django.db.models.functions import VectorDistance


class Product(models.Model):
    name = models.CharField(max_length=100)
    embedding = models.VectorField(dimensions=3)


Product.objects.create(name="Example", embedding=[0.9, 1.0, 0.95])
query_vector = [0.8, 1.0, 0.9]

distance = VectorDistance(
    "embedding",
    query_vector,
    distance=models.VectorDistanceType.COSINE,
)
nearest = Product.objects.annotate(distance=distance).order_by("distance", "pk")[:3]
nearby = Product.objects.alias(distance=distance).filter(distance__lt=0.2)
```

These queries are exact. The primary key gives a fixed order for equal
distances. Floating-point results can differ across database versions.

On backends supporting sparse `FLOAT32` storage and the requested metric,
sparse values use the same expression API:

```python
class SparseProduct(models.Model):
    embedding = models.VectorField(
        dimensions=30,
        storage_format=models.VectorStorageFormat.FLOAT32,
        storage_type=models.VectorStorageType.SPARSE,
    )


query = models.SparseVector(dimensions=30, indices=[3, 10, 12], values=[2.5, 2.5, 1.0])
SparseProduct.objects.create(embedding=query)
results = SparseProduct.objects.annotate(
    distance=VectorDistance(
        "embedding", query, distance=models.VectorDistanceType.EUCLIDEAN
    )
).filter(distance__lt=1.0)
```

### VectorIndex

```python
VectorIndex(
    fields,
    index_type,
    distance,
    name=None,
    accuracy=None,
    hnsw_neighbors=None,
    hnsw_efconstruction=None,
    ivf_neighbor_partitions=None,
    ivf_sample_per_partition=None,
    ivf_min_vectors_per_partition=None,
    parallel=None,
)
```

`VectorIndex` is an `Index` subclass declared in `Meta.indexes`. Its required
arguments are:

| Argument | Requirement |
| --- | --- |
| `fields` | Exactly one unprefixed name of a concrete `VectorField` on the model. The field must have fixed integer dimensions; `dimensions=VectorDimension.ANY` is not supported. |
| `index_type` | `VectorIndexType.HNSW` or `VectorIndexType.IVF`. |
| `distance` | A `VectorDistanceType` supported by the algorithm and storage format. No backend default is used. |

Expressions, descending field names, multi-column indexes, partial indexes,
covering columns, and unique indexes are not supported.

`name=None` uses Django's automatic index naming with a `vecidx` suffix.

The remaining options are backend-dependent:

- `accuracy` requests an integer target percentage from 1 to 100, not guaranteed
  recall or exact results. Recall is the proportion of exact nearest neighbors
  that an approximate search returns. This option is not limited to IVF.
- `hnsw_neighbors` and `hnsw_efconstruction` apply only to HNSW.
- `ivf_neighbor_partitions`, `ivf_sample_per_partition`, and
  `ivf_min_vectors_per_partition` apply only to IVF.
- `parallel` requests a degree of parallel execution. It does not guarantee a
  Python or database thread count across backends.

Equivalent pgvector options are:

| Django option | pgvector option |
| --- | --- |
| `hnsw_neighbors` | HNSW `m` |
| `hnsw_efconstruction` | HNSW `ef_construction` |
| `ivf_neighbor_partitions` | IVFFlat `lists` |

`VectorIndexType.IVF` identifies an index family, not a specific SQL name or
implementation. Backends must reject options without equivalents, not map them
to unrelated parameters.

Example declaration:

```python
class IndexedProduct(models.Model):
    embedding = models.VectorField(dimensions=128)

    class Meta:
        indexes = [
            models.VectorIndex(
                fields=["embedding"],
                name="product_embedding_hnsw",
                index_type=models.VectorIndexType.HNSW,
                distance=models.VectorDistanceType.COSINE,
            ),
        ]
```

Index construction may require substantial memory, existing data, and database
configuration. The example requires HNSW cosine indexing support. Not every
backend target supports this combination.

### Exact and approximate search

HNSW and IVF vector indexes support approximate nearest-neighbor (ANN) search.
Unlike ordinary indexes, they can change exact nearest-neighbor results.
The metric, query structure, and row-limiting syntax determine whether a query
can use an index. Creating an index does not guarantee that an ORM query uses it.

Ordinary `VectorDistance` annotations, threshold filters, and queryset slicing
must remain exact, even after a vector index is added. Each backend must provide
a tested exact execution strategy or reject the query.

Oracle may require an explicit exactness request when limiting rows. For
pgvector, tests must establish that an ordered distance query stays exact when
an ANN index is available.

Applications must explicitly request approximate queries. Documentation must
state that these queries can miss nearer rows and return fewer rows than requested.
An index's `accuracy` configures the index, not a Django query setting.
A target accuracy of 100 does not mean exact evaluation.

### Backend integration and unsupported environments

Each backend provides driver imports, capability detection, SQL types, value
binding and fetching, distance SQL, index DDL, and introspection through Django's
existing backend interfaces.

The implementation targets are:

| Backend | Integration and capability boundary |
| --- | --- |
| Oracle | Native vector types and operations, gated by server, driver, and client capabilities. |
| PostgreSQL | The pgvector extension, with extension-version checks and explicit installation prerequisites. Formats and index options without an equivalent remain unsupported. |
| SQLite | Provisional: SQLite-Vector is the candidate extension. The integration approach and supported capabilities remain to be established. |
| MySQL | Native `VECTOR` type. |
| MariaDB | Native `VECTOR` type. |

Declaring a field never installs or loads an extension. 

Backends must check vector storage, sparse storage, distance metrics, and index
support separately. Checks must include server versions, editions or distributions,
extensions, drivers, and client libraries. Where limits differ, check dimensions,
sparse nonzero entries, and index support separately.

The implementation uses ordinary field conversion, expression compilation,
and index/schema-editor interfaces. Each backend's parameter typing must
support `save()`, `update()`, `bulk_create()`, `bulk_update()`, and typed vector
literals in queries. Vector contents are bound as parameters. Metrics and
index options interpolated into SQL are validated enums or integers; table and
column identifiers use the schema editor's quoting mechanisms.

### Migrations, introspection, and serialization

Field and index deconstruction must preserve all options that affect behavior.
It must use stable import paths, enum members, and the `VectorDimension.ANY` sentinel.
`CreateModel`, `AddField`, `RemoveField`, `AddIndex`, and `RemoveIndex` must support
migration state and database operations. Introspection must distinguish vector
indexes from ordinary indexes for removal and renaming.

The initial implementation rejects database changes to vector dimensions,
storage format, or storage type with `NotSupportedError`. These changes can
lose data or require rebuilding the column and its indexes.

Renames and nullability changes follow the backend's tested behavior.

`inspectdb` must recover dimensions, format, and dense/sparse storage for
supported definitions. This includes `dimensions=models.VectorDimension.ANY` for
variable-dimensional columns. Generated comments must identify flexible formats
and other unsupported definitions. `inspectdb` must not substitute default field
settings.

`Field.value_to_string()` serializes vectors as JSON:

- Dense vectors: a list of numbers (byte values for `BINARY`).
- Sparse vectors: an object with `dimensions`, `indices`, and `values`.

`VectorField` does not provide a default form field.

## Rationale

### Preserve normal ORM expression semantics

[DEP 181][expressions] established composable ORM expressions. A vector distance
is a number, not a predicate. Thus, it uses an expression, not a lookup.
A `FloatField` output lets applications annotate, order, and filter distances.
Numeric comparisons remain separate from vector input conversion.

### Explicit defaults rather than database-dependent inference

A fixed `FLOAT32` default keeps schema declarations, Python values, and fixtures
consistent. Flexible scalar formats are deferred.

The distance expression defaults to Euclidean distance and always specifies the
metric. Oracle's [distance documentation][distance-docs] describes how indexes
can determine an omitted metric. Adding an index should not change a query's
mathematical meaning.

### Driver-independent Python values

Python lists, `array.array`, and `SparseVector` need no driver-specific values
or numerical package. Backend adapters convert native representations and sparse
index numbering.

### Community discussion and maintenance

The [initial ticket, 36517][ticket], was closed with a request to use the new
feature process, not a technical rejection of the API.

In issue 60, [Carlton Gibson requested a third-party package][package-request]
so Oracle users could test it and give feedback. Oracle contributors favored
integrated maintenance, easier discovery, and consistency with other ORM types.
[Other feedback][objections] questioned whether these benefits justify core
inclusion. It also noted the benefit of independent releases, especially for
applications on Django LTS releases.

The discussion also addressed limited maintenance capacity and Oracle sponsorship.
Neither the sponsorship discussion nor the linked email confirms technical
approval, funding, or an agreement to implement this DEP.

A related [Forum discussion about pgvectorscale][forum] shows the differences
between vector field compatibility, index DDL, and query-specific controls.

## Alternatives Considered

### Publish a cross-backend vector package first

A third-party package is the strongest alternative. Applications could test
field conversion, field and index APIs, and approximate search before Django
guarantees long-term compatibility.
[pgvector-python][pgvector] already provides Django fields, numeric distance
expressions, and HNSW/IVFFlat indexes for PostgreSQL.

Schema and driver integration may require a backend subclass or additional
Django hooks. If hooks are the only missing pieces, they should be proposed
separately.

### Common subset versus backend-specific APIs

An API limited to features shared by all backends would simplify portability.
However, shared features change with extension versions. This limit could exclude
useful sparse storage, metrics, or indexes.

Backend-specific APIs would provide all database features. But model declarations
and application values would depend on one backend, and APIs would duplicate
shared concepts.

This proposal shares behavior and Python values through one ORM API with explicit
capability checks. SQL and driver conversion remain backend-specific.
It does not replace or absorb `pgvector.django`.

### Ship only the field and exact distances

This option lets native storage and exact queries proceed independently of
approximate search. It is the preferred smaller scope if index capabilities or
the approximate-query API remain unresolved. A separate proposal could add
index declarations and approximate search.

### Keep raw SQL or use a dedicated vector service

Raw SQL gives immediate access to database features and database-specific tuning.
A separate vector service can provide scaling or retrieval features beyond a
relational field. Both are reasonable choices. Neither provides model, query,
and migration integration for vectors stored with existing relational rows.

## Backwards Compatibility

There is no automatic migration from other vector fields. Before changing to
Django's `VectorField`, compare database definitions and migration state.
Use a state-only migration only if no physical schema change is needed.

## Testing and Documentation

The implementation must include tests for:

- Supported scalar formats, fixed and `VectorDimension.ANY` dimensions, mixed-length
  dense rows, sparse indices and values, all-zero sparse values, nulls, and rounding.
- Rejection of omitted `dimensions`, `None` and string dimensions, invalid enums,
  booleans, range errors, NaN, and infinity.
- Assignment, `full_clean()`, save/read round trips, bulk operations, updates,
  fixtures, and migration serialization of fields, enums, and the `VectorDimension.ANY` sentinel.
- Literal and expression operands, aliases, annotations, numeric comparisons,
  ordering, null propagation, negative dot product, mismatched dimensions, and
  zero-vector cosine behavior.
- Field and index creation/removal, renames, introspection, unsupported
  alterations, index option validation, and migration-router behavior.
- Server, extension, driver, and client capability checks, and unsupported-feature
  errors. Shared imports and migration serialization must work without drivers.
  Non-vector parameter handling must not regress on any backend.
- Shared field and expression examples across backends. Python return types must
  be equivalent, and metric results must meet documented precision tolerances.
  Sparse adapters must preserve zero-based indices and enum meanings.

Documentation must cover:

- Backend support and Python value rules.
- Field and index references, and exact-query examples.
- Index deployment requirements, fixtures, and migrations.
- The difference between distance and similarity.
- [Exact and approximate search](#exact-and-approximate-search) behavior.

## References

- [New-features issue 60][feature] and the [linked sponsorship follow-up][email].
- [Trac ticket 36517][ticket].
- [DEP 181: ORM expressions][expressions].
- [python-oracledb: Using VECTOR Data][driver].
- [Oracle VECTOR_DISTANCE reference][distance-docs].
- [Oracle approximate similarity search][approximate] and
  [IVF query examples][ivf].
- [pgvector-python's Django integration][pgvector].
- [Forum: managing a table using pgvectorscale][forum].
- [MySQL VECTOR field][mysql-vector]. 
- [SQLite-vector][sqlite-vector]. 

[feature]: https://github.com/django/new-features/issues/60
[email]: https://github.com/django/new-features/issues/60#issuecomment-3259697145
[package-request]: https://github.com/django/new-features/issues/60#issuecomment-3104519246
[objections]: https://github.com/django/new-features/issues/60#issuecomment-3107078005
[ticket]: https://code.djangoproject.com/ticket/36517
[expressions]: https://github.com/django/deps/blob/main/final/0181-orm-expressions.rst
[driver]: https://python-oracledb.readthedocs.io/en/latest/user_guide/vector_data_type.html
[distance-docs]: https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/vector_distance.html
[approximate]: https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/understand-approximate-similarity-search-using-vector-indexes.html
[ivf]: https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/approximate-search-using-ivf.html
[pgvector]: https://github.com/pgvector/pgvector-python#django
[pgvector-variable]: https://github.com/pgvector/pgvector#can-i-store-vectors-with-different-dimensions-in-the-same-column
[forum]: https://forum.djangoproject.com/t/how-to-manage-a-table-created-outside-of-django/34228
[mysql-vector]: https://dev.mysql.com/doc/refman/9.7/en/vector.html 
[sqlite-vector]: https://github.com/sqliteai/sqlite-vector 

## Copyright

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(<http://creativecommons.org/publicdomain/zero/1.0/deed>).
