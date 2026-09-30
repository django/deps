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

This DEP proposes a shared Django ORM API for storing vectors and calculating
distances across supported database backends:

- `VectorField` stores dense or sparse vectors.
- `VectorDistance` calculates numeric distances.
- `VectorIndex` declares vector indexes.

Applications use common Python values, including `SparseVector`, and shared
enums. Backends handle database-specific storage, queries, and indexing.
Supported operations have consistent semantics, but capabilities may differ.
The API integrates with Django's existing validation, migrations, and
serialization.

Ordinary distance queries remain exact. Approximate search requires explicit
opt-in; its query API remains an open question. Embedding generation
and model-provider integrations are outside this proposal.

## Motivation

Applications store numeric embeddings to find semantically related documents,
similar images, or related products. For applications already keeping
source records in a relational database, a native vector column allows a query
to combine those records' ordinary filters with distance calculations, without
copying all candidate vectors into Python or synchronizing a separate vector
service.

The concrete gap is ORM integration with an existing database type, not an
embedding model or an AI workflow. JSON or binary fields can preserve vector
contents but do not provide the declared dimensions, native binding, distance
expressions, or index management of database vector types. Raw SQL can perform
these operations, but leaves applications responsible for conversion and
migration details.

## Specification

### Scope and public API

This draft specifies field storage, exact distance expressions, and vector index
declarations. The approximate-search query API remains unresolved. Shipping
indexes as an accelerated ORM search feature depends on resolving that API;
otherwise, the initial release would include only storage and exact distances.

The proposed public imports are:

```python
from django.db.models import (
    SparseVector,
    VectorDistanceType,
    VectorField,
    VectorIndex,
    VectorIndexType,
    VectorStorageFormat,
    VectorStorageType,
)
from django.db.models.functions import VectorDistance
```

`VectorField`, the enums, and `SparseVector` are defined in
`django.db.models.fields.vector` and re-exported from `django.db.models`.
Backends import these shared definitions, not each other’s constants or driver
types. `VectorDistance` is exported from `django.db.models.functions`.

Importing these APIs, declaring models, and serializing migration state must
not require any database driver or vector extension. Driver imports, native
value adaptation, SQL types, distance SQL, and index DDL belong in the respective
backends. No NumPy dependency is added.

The API describes the following capabilities; each backend implements its
supported subset:

- Dense `FLOAT32`, `FLOAT64`, `INT8`, and packed `BINARY` vectors.
- Sparse `FLOAT32`, `FLOAT64`, and `INT8` vectors.
- Explicit distance calculations, including numeric threshold filtering.
- Migration-managed hierarchical navigable small world (HNSW) and inverted file
  (IVF) vector indexes where supported.

**Out of scope:** Embedding generation, vector arithmetic and aggregation,
automatic normalization, hybrid full-text search, reranking, and cross-database
fallback storage.

**Backend targets:** Oracle, PostgreSQL with pgvector, and MySQL. SQLite is also
an intended target, but its extension choice is provisional. Other backends can
implement the same API. The backend integration section defines capability
checks and behavior for unsupported operations.

### VectorField

```python
VectorField(
    dim=6,
    storage_format=VectorStorageFormat.FLOAT32,
    storage_type=VectorStorageType.DENSE,
    **options,
)
```

`options` are ordinary model field options, subject to the restrictions below.
The additional arguments have these meanings:

| Argument | Meaning |
| --- | --- |
| `dim` | Required. A positive integer number of dimensions, or the `VectorField.ANY` sentinel for variable-dimensional dense storage. There is no default; omitting `dim` raises `TypeError`. Booleans, `None`, and strings such as `"*"` or `"ANY"` are not valid dimensions. |
| `storage_format` | One of `FLOAT32`, `FLOAT64`, `INT8`, or `BINARY` from `VectorStorageFormat`. The default is `FLOAT32`. |
| `storage_type` | `VectorStorageType.DENSE` or `VectorStorageType.SPARSE`. The default is `DENSE`. |

The enums have stable string values matching their member names and must be
serializable in migrations. This draft accepts enum members, not arbitrary SQL
strings. Explicit `None` is not accepted for either storage argument. Flexible
scalar formats and mixed dense/sparse columns are deferred; only `dim` accepts
`VectorField.ANY` in the initial API.

`VectorField.ANY` is a public singleton sentinel scoped to `VectorField`, not 
a SQL string or a vector value. It means that the column may store vectors with 
different numbers of dimensions. 

`VectorField(dim=3)` maps to Oracle’s `VECTOR(3, FLOAT32, DENSE)` or pgvector’s
`vector(3)`. `VectorField(dim=VectorField.ANY)` maps to
Oracle’s `VECTOR(*, FLOAT32, DENSE)` or pgvector’s `vector` without a dimension
modifier, as described in the [pgvector documentation][pgvector-variable].
These mappings use the default dense `FLOAT32` storage; other formats require
separate backend capability checks.

```python
from django.db import models


class VariableProduct(models.Model):
    embedding = models.VectorField(dim=models.VectorField.ANY)


VariableProduct.objects.create(embedding=[0.1, 0.2, 0.3])
VariableProduct.objects.create(embedding=[0.1, 0.2])
```

Each value still has a concrete, nonzero dimension. Distance operands must
have equal actual dimensions; `VectorField.ANY` does not make differently sized vectors
comparable.

Field declarations have these restrictions:

- Sparse fields require a positive integer `dim`; `VectorField.ANY` is not supported.
- Sparse `BINARY` storage is not supported.
- Binary dimensions count bits and, when specified, must be a multiple of eight.

Empty vectors are not treated as `NULL` or zero vectors.
`empty_strings_allowed` is false.

The initial implementation rejects `primary_key=True`, `unique=True`, and
`db_index=True`. Vector indexes are declared using `Meta.indexes`, not ordinary
B-tree indexing. Vector columns are not supported as foreign-key targets.
Unsupported vector constraints and ordinary indexes on vector columns must
produce system check errors rather than silently producing a different schema.

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

Dense floating-point lists may contain integers or floats, but not booleans.
Integer and binary formats reject fractional input values rather than truncating them.
Non-finite values and overflow in the destination format are rejected. Floating-point
rounding to the declared precision is expected and documented.

An array must have the type code appropriate to the field. An incorrectly
typed array is rejected rather than implicitly reinterpreted. A fixed-dimensional
numeric vector must contain `dim` components; a binary vector must contain
`dim / 8` bytes. For example, `[180, 150, 100]` represents a 24-dimensional
binary vector, not a three-dimensional vector. Variable-dimensional dense
vectors still must be nonempty and respect the database's maximum dimensions.

#### Sparse values

Sparse values require the common `SparseVector` class.

Its dimension must match the field.
Indices are zero-based integers, strictly increasing, unique, and less than
`dim`; their count must equal the count of values. Values use the field's
format and may be a list or appropriately typed array. Explicit zero entries
are rejected; an all-zero sparse vector is represented by empty indices and
values, subject to the backend capability tests described below. 
No automatic sorting, duplicate merging, densification, or sparsification takes
place.

Sparse database reads and sparse `to_python()` normalization return the common
`SparseVector`, never a database driver's sparse class:

```python
from django.db.models import SparseVector

query = SparseVector(dim=30, indices=[3, 10, 12], values=[2.5, 2.5, 1.0])
```

`SparseVector(dim, indices, values)` follows the validation rules above and
exposes those three attributes. The constructor accepts a list or appropriately
typed array for `values`; the field performs format-specific validation. After
field normalization through `to_python()`, `indices` is a tuple of integers and
`values` is an `array.array` with the field's type code. Database reads return
this same representation. The constructor does not select a field's storage
format; format-specific conversion occurs during field normalization. Backends
handle driver conversion and preserve zero-based indices in Python.

Convenience tuples are not accepted for sparse values, avoiding ambiguity with
dense sequences. NumPy users explicitly convert their data to lists or supported
arrays.

### Distance expressions

```python
VectorDistance(lhs, rhs, distance=VectorDistanceType.EUCLIDEAN)
```

`VectorDistance` accepts vector-valued expressions and literals (lists, arrays,
or `SparseVector` instances). Literals are wrapped in
`Value` expressions using the other operand’s resolved `VectorField`. If neither
operand provides that type, callers must supply explicitly typed `Value`
expressions; otherwise resolution raises `FieldError`.

The operands must have matching dimensions, scalar formats, and storage types.
Known incompatibilities are rejected during expression resolution or literal
preparation. For variable-dimensional columns and other properties only known
at execution, database errors are exposed through Django's database exception
wrapping. The common contract prohibits mixed dense/sparse comparisons; there
is no implicit conversion even if a particular database permits one.

The result's output field is `FloatField`, and non-null database results are
returned as Python floats. If either operand is SQL `NULL`, the result is
`None`. Null ordering uses Django's ordinary expression ordering API.

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
distances, such as cosine distance involving a zero vector. Each backend’s
behavior must be documented and tested. 

`EUCLIDEAN` is the default. Django always specifies the metric in SQL rather
than relying on database defaults or index-based inference. Passing anything
other than a `VectorDistanceType` member raises `TypeError`.

Example:

```python
from django.db import models
from django.db.models.functions import VectorDistance


class Product(models.Model):
    name = models.CharField(max_length=100)
    embedding = models.VectorField(dim=3)


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

These are exact queries. The primary-key ordering provides a deterministic
secondary ordering for equal distances; floating-point equality across database
versions is not promised.

On backends supporting sparse `FLOAT32` storage and the requested metric,
sparse values use the same expression API:

```python
class SparseProduct(models.Model):
    embedding = models.VectorField(
        dim=30,
        storage_format=models.VectorStorageFormat.FLOAT32,
        storage_type=models.VectorStorageType.SPARSE,
    )


query = models.SparseVector(dim=30, indices=[3, 10, 12], values=[2.5, 2.5, 1.0])
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
| `fields` | Exactly one unprefixed name of a concrete `VectorField` on the model. The field must have fixed integer dimensions; `dim=VectorField.ANY` is not supported. |
| `index_type` | `VectorIndexType.HNSW` or `VectorIndexType.IVF`. |
| `distance` | A `VectorDistanceType` supported by the algorithm and storage format. No backend default is used. |

Expressions, descending field names, multi-column indexes, partial indexes,
covering columns, and unique indexes are not supported.

`name=None` uses Django’s automatic index naming with a `vecidx` suffix.

The remaining options are backend-dependent:

- `accuracy` requests target accuracy as an integer percentage from 1 to 100.
  It is not a guarantee of recall or exact results. Recall is the proportion of
  the exact nearest neighbors returned by an approximate search. This option is
  not restricted to IVF.
- `hnsw_neighbors` and `hnsw_efconstruction` apply only to HNSW.
- `ivf_neighbor_partitions`, `ivf_sample_per_partition`, and
  `ivf_min_vectors_per_partition` apply only to IVF.
- `parallel` specifies the requested degree of parallel execution, not a
  portable promise about the number of Python or database threads.

Backends map only equivalent options. For pgvector:

| Django option | pgvector option |
| --- | --- |
| `hnsw_neighbors` | HNSW `m` |
| `hnsw_efconstruction` | HNSW `ef_construction` |
| `ivf_neighbor_partitions` | IVFFlat `lists` |

`VectorIndexType.IVF` identifies an index family, not a specific SQL spelling or
implementation. Options without equivalents must be rejected, not mapped to
unrelated tuning parameters.

Example declaration:

```python
class IndexedProduct(models.Model):
    embedding = models.VectorField(dim=128)

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
Unlike ordinary indexes, they do not necessarily preserve an exact
nearest-neighbor result. Metric selection,
query shape, and row-limiting syntax affect index eligibility. Creating an index
therefore does not establish that a particular ORM query will use it.

Ordinary `VectorDistance` annotations, threshold filters, and queryset slicing
must remain exact, even after a vector index is added. Each backend must provide
a tested exact execution strategy or reject the query.

Oracle may require an explicit exactness request when limiting rows. For
pgvector, tests must establish that an ordered distance query stays exact when
an ANN index is available.

An approximate query must be an explicit opt-in, and must document that it can
miss nearer rows and may return fewer than the requested number. An index's
`accuracy` configures the index, not a query-level Django setting. A target
accuracy of 100 must not be described as equivalent to exact evaluation.

Until that design is settled, the field and exact expression can be developed
independently. The draft does not claim that its ordinary sliced query example
exercises HNSW or IVF. Shipping index support as an accelerated ORM search
feature requires resolving this question, or explicitly reducing the initial
release scope to field storage and exact distance calculations.

### Backend integration and unsupported environments

Each backend provides capability detection, SQL types, value binding and
fetching, distance SQL, index DDL, and introspection through Django’s existing
backend interfaces.

The implementation targets are:

| Backend | Integration and capability boundary |
| --- | --- |
| Oracle | Native vector types and operations, gated by server, driver, and client capabilities. |
| PostgreSQL | The pgvector extension, with extension-version checks and explicit installation prerequisites. Formats and index options without an equivalent remain unsupported. |
| SQLite | Provisional: SQLite-Vector is the candidate extension. The integration approach and supported capabilities remain to be established. |
| MySQL | Native `VECTOR` type. |

Declaring a field never installs or loads an extension. 

Backends must distinguish vector storage, sparse storage, distance metrics,
and indexing support. Feature detection must account for server versions,
editions or distributions, extensions, drivers, and client libraries. Dimension
limits, sparse nonzero limits, and indexability must be checked separately where
they differ.

Unsupported options must be rejected rather than silently changing behavior.
Backends must not downcast values, substitute dense storage for sparse storage,
or change the requested dimension policy.

Field checks honor the selected database aliases and migration routers.
Unsupported databases receive an actionable check error where the model is
expected to be used. Schema creation, value adaptation, and SQL compilation
also raise `django.db.NotSupportedError` when the corresponding feature is
unavailable. Django never substitutes JSON, text, or binary storage, and never
silently skips a requested vector index.

The implementation uses ordinary field conversion, expression compilation,
and index/schema-editor interfaces. Each backend's parameter typing must
support `save()`, `update()`, `bulk_create()`, `bulk_update()`, and typed vector
literals in queries. Vector contents are bound as parameters. Metrics and
index options interpolated into SQL are validated enums or integers; table and
column identifiers use the schema editor's quoting mechanisms.

### Migrations, introspection, and serialization

Field and index deconstruction must preserve every semantic option, using
stable import paths, enum members, and the `VectorField.ANY` sentinel. `CreateModel`, `AddField`, `RemoveField`,
`AddIndex`, and `RemoveIndex` must work in migration state and database operations.
Index introspection must identify vector indexes so removal and renaming do
not mistake them for ordinary indexes.

The initial implementation rejects database changes to vector dimensions,
storage format, or storage type with `NotSupportedError`. These changes can
lose data or require rebuilding the column and its indexes.

To change a vector definition:

1. Add a new field.
2. Backfill it and validate the data.
3. Replace the indexes.
4. Remove the old field.

Renames and nullability changes follow the backend’s tested behavior.

`inspectdb` must recover dimensions, format, and dense/sparse storage for
supported definitions, including `dim=models.VectorField.ANY` for variable-dimensional
columns. If it encounters a flexible format or other definition
outside this contract, it must identify the unsupported definition in generated
comments rather than silently substitute the default field configuration.

`value_to_string()` serializes vectors as JSON:

- Dense vectors: a list of numbers (byte values for `BINARY`).
- Sparse vectors: an object with `dim`, `indices`, and `values`.

`VectorField` does not provide a default form field.

## Rationale

### Preserve normal ORM expression semantics

[DEP 181][expressions] established composable ORM expressions. A vector distance
is a number, not a predicate, so it fits an expression rather than a lookup. A
`FloatField` output lets applications annotate, order, and filter distances using
the existing ORM, while keeping numeric comparisons separate from vector input
conversion.

### Explicit defaults rather than database-dependent inference

A fixed `FLOAT32` default keeps schema declarations, Python values, and fixtures
consistent. Flexible scalar formats are deferred.

The distance expression defaults to Euclidean distance and always emits the
metric explicitly. Oracle's [distance documentation][distance-docs] describes
omitted-metric inference involving indexes. A query's mathematical meaning
should not change as a side effect of adding an index.

### Driver-independent Python values

Python lists, `array.array` and `SparseVector` avoid driver-specific application 
values without requiring a numerical package. Backend adapters handle native 
representations and sparse index numbering.

### Community discussion and maintenance

The [initial ticket, 36517][ticket], was closed with a request to use the new
feature process. That was a process referral, not a technical rejection of the
API.

In issue 60, [Carlton Gibson requested a third-party package][package-request]
so Oracle users could experiment and provide feedback. Oracle contributors
argued for integrated maintenance, discoverability, and consistency with other
ORM-supported types. [Other feedback][objections] challenged whether those
benefits justify core inclusion and noted that independent releases can be an
advantage, especially for applications on Django LTS releases.

The discussion also raised the project's limited maintenance capacity and
Oracle sponsorship. These are relevant sustainability concerns, but neither
a sponsorship conversation nor the linked email follow-up constitutes technical
approval, a funding commitment, or agreement to implement this DEP.

A related [Forum discussion about pgvectorscale][forum] illustrates the
distinction between vector field compatibility, index DDL, and query-specific
controls.

## Alternatives Considered

### Publish a cross-backend vector package first

A third-party package is the strongest alternative. It would let applications
test field conversion, field and index APIs, and approximate search before
Django commits to long-term compatibility guarantees.
[pgvector-python][pgvector] already provides Django fields, numeric distance
expressions, and HNSW/IVFFlat indexes for PostgreSQL.

Schema and driver integration may require a backend subclass or additional
Django hooks. If hooks are the only missing pieces, they should be proposed
separately.

### Common subset versus backend-specific APIs

Limiting the API to features shared by every backend would simplify portability,
but that intersection changes with extension versions and may exclude useful
sparse storage, metrics, or indexing.

Backend-specific APIs would expose each database’s full feature set, but tie
model declarations and application values to that backend and duplicate common
concepts.

This proposal instead shares behavior and Python values through a common ORM
API, with explicit capability checks. SQL and driver adaptation remain
backend-specific. It does not replace or absorb `pgvector.django`.

### Ship only the field and exact distances

This provides useful native storage and threshold queries without adding
approximate query semantics. It also avoids suggesting that ordinary queryset
slices automatically benefit from HNSW or IVF. It is the preferred scope
reduction if the index capability matrix and approximate-query contract cannot
be settled for the initial release. Index declarations and approximate search
could follow as a separate proposal.

### Keep raw SQL or use a dedicated vector service

Raw SQL exposes database features immediately and permits database-specific
tuning. A separate vector service can offer scaling or retrieval features
outside the scope of a relational field. Both remain reasonable application
choices. Neither provides the particular benefit proposed here: model, query,
and migration integration for vectors stored alongside existing relational rows.

## Backwards Compatibility

There is no automatic migration from other vector-field implementations. Before
switching to Django’s `VectorField`, compare the database definitions and
migration state. Use a state-only migration only if that comparison confirms no
physical schema change is needed.

## Testing and Documentation

The implementation must include tests for:

- Every supported scalar format, fixed and `VectorField.ANY` dimensions, mixed-length dense
  rows, rejection of omitted `dim`, `None`, and string dimensions, sparse indices 
  and values, all-zero sparse values, nulls, invalid enums, booleans, range errors, 
  NaN, infinity, and precision rounding.
- Assignment, `full_clean()`, save/read round trips, bulk operations, updates,
  fixtures, and migration serialization of fields, enums, and the `VectorField.ANY` sentinel.
- Literal and expression operands, aliases, annotations, numeric comparisons,
  ordering, null propagation, negative dot product, mismatched dimensions, and
  zero-vector cosine behavior.
- Field and index creation/removal, renames, introspection, unsupported
  alterations, index option validation, and migration-router behavior.
- Server, extension, driver, and client feature gates, unsupported capability
  errors, common imports and migration serialization without database drivers,
  and no regression in non-vector parameter handling on any backend.
- The same supported field and expression examples on multiple backends, with
  equivalent Python return types and metric results within documented precision
  tolerances. Sparse adapters must preserve zero-based indices and enum meanings.

Documentation must include the support matrix, Python value contract, field and
index references, exact-query examples, index deployment prerequisites, fixture
and migration guidance, and the distinction between distance and similarity.
Approximate-query documentation must not imply that a vector index is used
merely because a query orders by distance.

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
