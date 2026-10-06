"use client";

import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useId, useRef } from "react";

import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";
import { toEditorHtml } from "@/lib/rich-text";

type RichTextEditorProps = {
  id?: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
};

export function RichTextEditor({
  id,
  label,
  value,
  onChange,
  placeholder,
  required,
  error,
}: RichTextEditorProps) {
  const generatedId = useId();
  const editorId = id ?? generatedId;
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const editor = useEditor({
    immediatelyRender: false,
    shouldRerenderOnTransaction: true,
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        code: false,
        codeBlock: false,
        horizontalRule: false,
        strike: false,
      }),
      Placeholder.configure({
        placeholder: placeholder ?? "",
      }),
    ],
    content: toEditorHtml(value),
    editorProps: {
      attributes: {
        id: editorId,
        role: "textbox",
        "aria-multiline": "true",
        "aria-required": required ? "true" : "false",
        "aria-invalid": error ? "true" : "false",
        "aria-labelledby": `${editorId}-label`,
        class: "rich-text min-h-36 px-3.5 py-2.5 text-body-md text-on-surface outline-none",
      },
    },
    onUpdate: ({ editor: current }) => {
      onChangeRef.current(current.isEmpty ? "" : current.getHTML());
    },
  });

  return (
    <div className="min-w-0 max-w-full">
      <label
        className="mb-1.5 block min-w-0 text-label-md font-medium break-words text-on-surface"
        htmlFor={editorId}
        id={`${editorId}-label`}
      >
        {label}
        {required ? (
          <span className="text-error" aria-hidden>
            {" "}
            *
          </span>
        ) : null}
      </label>
      <div
        className={cn(
          "overflow-hidden rounded-md border bg-surface-container-lowest transition duration-150",
          error
            ? "border-error focus-within:ring-[3px] focus-within:ring-error/15"
            : "border-outline-variant focus-within:border-secondary focus-within:ring-[3px] focus-within:ring-secondary/15",
        )}
      >
        <div className="flex flex-wrap items-center gap-0.5 border-b border-outline-variant bg-surface-container-low px-1.5 py-1">
          <FormatButton
            active={editor?.isActive("bold") ?? false}
            disabled={!editor}
            icon="format_bold"
            label="Bold"
            onClick={() => editor?.chain().focus().toggleBold().run()}
          />
          <FormatButton
            active={editor?.isActive("italic") ?? false}
            disabled={!editor}
            icon="format_italic"
            label="Italic"
            onClick={() => editor?.chain().focus().toggleItalic().run()}
          />
          <FormatButton
            active={editor?.isActive("heading", { level: 2 }) ?? false}
            disabled={!editor}
            icon="title"
            label="Heading"
            onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
          />
          <FormatButton
            active={editor?.isActive("bulletList") ?? false}
            disabled={!editor}
            icon="format_list_bulleted"
            label="Bulleted list"
            onClick={() => editor?.chain().focus().toggleBulletList().run()}
          />
          <FormatButton
            active={editor?.isActive("orderedList") ?? false}
            disabled={!editor}
            icon="format_list_numbered"
            label="Numbered list"
            onClick={() => editor?.chain().focus().toggleOrderedList().run()}
          />
        </div>
        <EditorContent editor={editor} />
      </div>
      {error ? <p className="mt-1 text-body-sm text-error">{error}</p> : null}
    </div>
  );
}

function FormatButton({
  active,
  disabled,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  disabled: boolean;
  icon: string;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      aria-label={label}
      aria-pressed={active}
      className={cn(
        "rounded p-1 text-on-surface-variant hover:bg-surface-container hover:text-on-surface disabled:opacity-40",
        active ? "bg-surface-container text-secondary" : null,
      )}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      <Icon className="text-[18px]" name={icon} />
    </button>
  );
}
