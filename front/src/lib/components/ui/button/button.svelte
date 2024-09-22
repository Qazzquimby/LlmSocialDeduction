<script lang="ts">
	import { Button as ButtonPrimitive } from "bits-ui";
	import { type Events, type Props } from "./index.js";

	type $$Props = Props;
	type $$Events = Events;

	let className: $$Props["class"] = undefined;
	export { className as class };
</script>

<ButtonPrimitive.Root
	class="bg-dark-700 hover:bg-dark-300 text-gray-100 px-4 py-2 rounded transition-colors duration-200 {className}"
	type="button"
	{...$$restProps}
	on:click
	on:keydown
>
	<slot />
</ButtonPrimitive.Root>
