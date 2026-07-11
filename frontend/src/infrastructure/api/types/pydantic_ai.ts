import { z } from "zod";

/* -------------------------------------------------------------------------- */
/* Shared                                                                     */
/* -------------------------------------------------------------------------- */

const TimestampSchema = z.string();

const NullableStringSchema = z.string().nullish();

const RecordSchema = z.record(
  z.string(),
  z.unknown(),
);

const ToolPartKindSchema = z
  .enum([
    "tool-search",
    "capability-load",
  ])
  .nullish();

/* -------------------------------------------------------------------------- */
/* User content                                                               */
/* -------------------------------------------------------------------------- */

const FileUrlFields = {
  url: z.string(),

  force_download: z
    .union([
      z.boolean(),
      z.literal("allow-local"),
    ])
    .optional(),

  vendor_metadata: RecordSchema.nullish(),

  identifier: z.string().optional(),
  media_type: z.string().optional(),
};

const ImageUrlSchema = z.looseObject({
  ...FileUrlFields,
  kind: z.literal("image-url"),
});

const AudioUrlSchema = z.looseObject({
  ...FileUrlFields,
  kind: z.literal("audio-url"),
});

const VideoUrlSchema = z.looseObject({
  ...FileUrlFields,
  kind: z.literal("video-url"),
});

const DocumentUrlSchema = z.looseObject({
  ...FileUrlFields,
  kind: z.literal("document-url"),
});

const BinaryContentSchema = z.looseObject({
  data: z.string(),
  media_type: z.string(),

  vendor_metadata: RecordSchema.nullish(),
  identifier: z.string().optional(),

  kind: z.literal("binary"),
});

const UploadedFileSchema = z.looseObject({
  file_id: z.string(),

  provider_name: z.enum([
    "anthropic",
    "openai",
    "google",
    "google-cloud",
    "google-gla",
    "google-vertex",
    "bedrock",
    "xai",
  ]),

  vendor_metadata: RecordSchema.nullish(),
  identifier: z.string().optional(),
  media_type: z.string().optional(),

  kind: z.literal("uploaded-file"),
});

const MultiModalContentSchema = z.discriminatedUnion(
  "kind",
  [
    ImageUrlSchema,
    AudioUrlSchema,
    VideoUrlSchema,
    DocumentUrlSchema,
    BinaryContentSchema,
    UploadedFileSchema,
  ],
);

const TextContentSchema = z.looseObject({
  content: z.string(),
  metadata: z.unknown().nullish(),
  kind: z.literal("text-content"),
});

const CachePointSchema = z.looseObject({
  kind: z.literal("cache-point"),
  ttl: z.enum(["5m", "1h"]).optional(),
});

const UserContentSchema = z.union([
  z.string(),
  TextContentSchema,
  MultiModalContentSchema,
  CachePointSchema,
]);

/* -------------------------------------------------------------------------- */
/* Request parts                                                              */
/* -------------------------------------------------------------------------- */

const SystemPromptPartSchema = z.looseObject({
  content: z.string(),
  timestamp: TimestampSchema,
  dynamic_ref: NullableStringSchema,
  part_kind: z.literal("system-prompt"),
});

const UserPromptPartSchema = z.looseObject({
  content: z.union([
    z.string(),
    z.array(UserContentSchema),
  ]),

  timestamp: TimestampSchema,

  part_kind: z.literal("user-prompt"),
});

const ToolReturnPartSchema = z.looseObject({
  tool_name: z.string(),

  /*
   * Tool returns may contain arbitrary serializable values,
   * including multimodal content.
   */
  content: z.unknown(),

  tool_call_id: z.string(),
  tool_kind: ToolPartKindSchema,

  metadata: z.unknown().nullish(),
  timestamp: TimestampSchema,

  outcome: z
    .enum([
      "success",
      "failed",
      "denied",
    ])
    .optional(),

  files: z
    .array(MultiModalContentSchema)
    .optional(),

  part_kind: z.literal("tool-return"),
});

const ErrorDetailsSchema = z.looseObject({
  type: z.string(),

  loc: z.array(
    z.union([
      z.string(),
      z.number().int(),
    ]),
  ),

  msg: z.string(),

  input: z.unknown().optional(),
  ctx: RecordSchema.optional(),
  url: z.string().optional(),
});

const RetryPromptPartSchema = z.looseObject({
  content: z.union([
    z.string(),
    z.array(ErrorDetailsSchema),
  ]),

  tool_name: NullableStringSchema,
  tool_call_id: z.string(),
  timestamp: TimestampSchema,

  part_kind: z.literal("retry-prompt"),
});

const ModelRequestPartSchema = z.discriminatedUnion(
  "part_kind",
  [
    SystemPromptPartSchema,
    UserPromptPartSchema,
    ToolReturnPartSchema,
    RetryPromptPartSchema,
  ],
);

/* -------------------------------------------------------------------------- */
/* Response parts                                                             */
/* -------------------------------------------------------------------------- */

const ProviderPartFields = {
  id: NullableStringSchema,
  provider_name: NullableStringSchema,
  provider_details: RecordSchema.nullish(),
};

const TextPartSchema = z.looseObject({
  content: z.string(),

  ...ProviderPartFields,

  part_kind: z.literal("text"),
});

const ThinkingPartSchema = z.looseObject({
  content: z.string(),

  id: NullableStringSchema,
  signature: NullableStringSchema,
  provider_name: NullableStringSchema,
  provider_details: RecordSchema.nullish(),

  part_kind: z.literal("thinking"),
});

const CompactionPartSchema = z.looseObject({
  content: z.string().nullish(),

  ...ProviderPartFields,

  part_kind: z.literal("compaction"),
});

const FilePartSchema = z.looseObject({
  content: BinaryContentSchema,

  ...ProviderPartFields,

  part_kind: z.literal("file"),
});

const ToolCallFields = {
  tool_name: z.string(),

  args: z
    .union([
      z.string(),
      RecordSchema,
    ])
    .nullish(),

  tool_call_id: z.string(),
  tool_kind: ToolPartKindSchema,

  id: NullableStringSchema,
  provider_name: NullableStringSchema,
  provider_details: RecordSchema.nullish(),
};

const ToolCallPartSchema = z.looseObject({
  ...ToolCallFields,
  part_kind: z.literal("tool-call"),
});

const NativeToolCallPartSchema = z.looseObject({
  ...ToolCallFields,
  part_kind: z.literal("builtin-tool-call"),
});

const NativeToolReturnPartSchema = z.looseObject({
  tool_name: z.string(),
  content: z.unknown(),

  tool_call_id: z.string(),
  tool_kind: ToolPartKindSchema,

  metadata: z.unknown().nullish(),
  timestamp: TimestampSchema,

  outcome: z
    .enum([
      "success",
      "failed",
      "denied",
    ])
    .optional(),

  provider_name: NullableStringSchema,
  provider_details: RecordSchema.nullish(),

  files: z
    .array(MultiModalContentSchema)
    .optional(),

  part_kind: z.literal("builtin-tool-return"),
});

const ModelResponsePartSchema = z.discriminatedUnion(
  "part_kind",
  [
    TextPartSchema,
    ThinkingPartSchema,
    CompactionPartSchema,
    FilePartSchema,
    ToolCallPartSchema,
    NativeToolCallPartSchema,
    NativeToolReturnPartSchema,
  ],
);

/* -------------------------------------------------------------------------- */
/* Messages                                                                   */
/* -------------------------------------------------------------------------- */

const RequestUsageSchema = z
  .looseObject({
    input_tokens: z
      .number()
      .int()
      .nonnegative(),

    cache_write_tokens: z
      .number()
      .int()
      .nonnegative(),

    cache_read_tokens: z
      .number()
      .int()
      .nonnegative(),

    output_tokens: z
      .number()
      .int()
      .nonnegative(),

    input_audio_tokens: z
      .number()
      .int()
      .nonnegative(),

    cache_audio_read_tokens: z
      .number()
      .int()
      .nonnegative(),

    output_audio_tokens: z
      .number()
      .int()
      .nonnegative(),

    details: z.record(
      z.string(),
      z.number().int(),
    ),

    total_tokens: z
      .number()
      .int()
      .nonnegative()
      .optional(),
  })
  .partial();

const ModelRequestSchema = z.looseObject({
  parts: z.array(ModelRequestPartSchema),

  timestamp: TimestampSchema.nullish(),
  instructions: NullableStringSchema,

  kind: z.literal("request"),

  run_id: NullableStringSchema,
  conversation_id: NullableStringSchema,
  metadata: RecordSchema.nullish(),

  state: z
    .enum([
      "complete",
      "interrupted",
    ])
    .optional(),
});

const ModelResponseSchema = z.looseObject({
  parts: z.array(ModelResponsePartSchema),

  usage: RequestUsageSchema.optional(),

  model_name: NullableStringSchema,
  timestamp: TimestampSchema,

  kind: z.literal("response"),

  provider_name: NullableStringSchema,
  provider_url: NullableStringSchema,
  provider_details: RecordSchema.nullish(),
  provider_response_id: NullableStringSchema,

  finish_reason: z
    .enum([
      "stop",
      "length",
      "content_filter",
      "tool_call",
      "error",
    ])
    .nullish(),

  run_id: NullableStringSchema,
  conversation_id: NullableStringSchema,
  metadata: RecordSchema.nullish(),

  state: z
    .enum([
      "complete",
      "incomplete",
      "interrupted",
    ])
    .optional(),
});

/* -------------------------------------------------------------------------- */
/* Public API                                                                 */
/* -------------------------------------------------------------------------- */

export const ModelMessageSchema = z.discriminatedUnion(
  "kind",
  [
    ModelRequestSchema,
    ModelResponseSchema,
  ],
);

export const ModelMessagesSchema = z.array(
  ModelMessageSchema,
);

export type ModelMessage = z.infer<
  typeof ModelMessageSchema
>;

export type ModelMessages = z.infer<
  typeof ModelMessagesSchema
>;